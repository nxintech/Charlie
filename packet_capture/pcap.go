package gopacket

import (
	"log"
	"flag"
	"time"
	"github.com/google/gopacket"
	"github.com/google/gopacket/pcap"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/tcpassembly"
)

// https://youtu.be/APDnbmTKjgM
// https://www.devdungeon.com/content/packet-capture-injection-and-analysis-gopacket

var (
	iface    = flag.String("i", "eth0", "Interface to get packets from")
	filter   = flag.String("f", "tcp", "BPF filter for pcap")
	port     = flag.String("p", "", "Port to filter")
	interval = flag.String("interval", "1s", "log interval. Any string parsed by time.ParseDuration is acceptable here")

	eth layers.Ethernet
	ip4 layers.IPv4
	tcp layers.TCP
	payload gopacket.Payload
)

// implements tcpassembly.StreamFactory interface
type streamFactory struct{}

// New creates a new stream.  It's called whenever the assembler sees a stream
// it isn't currently following.
func (factory *streamFactory) New(net, transport gopacket.Flow) tcpassembly.Stream {
	log.Printf("new stream %v:%v->%v:%v started", net.Src(), transport.Src(),
		net.Dst(), transport.Dst())
	s := &Stream{
		net:       net,
		transport: transport,
		start:     time.Now(),
	}
	//s.end = s.start
	// ReaderStream implements tcpassembly.Stream, so we can return a pointer to it.
	return s
}

// statsStream will handle the actual decoding of stats requests.
// implements tcpassembly.Stream interface
type Stream struct {
	net            gopacket.Flow
	transport      gopacket.Flow
	bytes, packets int64
	start, end     time.Time
}

// Reassembled is called whenever new packet data is available for reading.
// Reassembly objects contain stream data IN ORDER.
func (s *Stream) Reassembled(reassemblies []tcpassembly.Reassembly) {
	for _, reassembly := range reassemblies {

		s.bytes += int64(len(reassembly.Bytes))
		s.packets += 1
	}
}

// ReassemblyComplete is called when the TCP assembler believes a stream has
// finished.
func (s *Stream) ReassemblyComplete() {
	log.Printf("%v:%v->%v:%v %v",
		s.net.Src(), s.transport.Src(), s.net.Dst(), s.transport.Dst(), s.bytes)
}

// Set up pcap packet capture
func NewHandle() (*pcap.Handle, error) {
	// http://www.tcpdump.org/pcap.html
	// pcap_t *pcap_open_live(char *device, int snaplen,
	// 						  int promisc, int to_ms, char *ebuf)
	// snaplen is an integer which defines the maximum number
	// of bytes to be captured by pcap
	// promisc promiscuous mode
	// to_ms is the read time out in milliseconds
	// 		a value of 0 means no time out
	// ebuf is a string we can store any error messages
	// p.cptr = C.pcap_open_live(dev, C.int(snaplen), pro, timeoutMillis(timeout), buf)
	// buf := (*C.char)(C.calloc(errorBufferSize, 1)) //  256
	handle, err := pcap.OpenLive(*iface, int32(65536), true, 0)
	if err != nil {
		log.Fatal("error opening pcap handle: ", err)
		return nil, err
	}

	if len(*port) > 0 {
		v := *filter + " " + *port
		filter = &v
	}

	err = handle.SetBPFFilter(*filter)
	if err != nil {
		log.Fatal("error setting BPF filter: ", err)
		return nil, err
	}

	return handle, nil
}

func main() {
	intervalDuration, err := time.ParseDuration(*interval)
	if err != nil {
		log.Fatal("invalid interval duration: ", *interval)
	}

	log.Printf("starting capture on interface %q", *iface)

	handle, err := NewHandle()
	if err != nil {
		log.Fatal("error NewHandle: ", err)
	}

	// Set up assembly
	streamPool := tcpassembly.NewStreamPool(&streamFactory{})
	assembler := tcpassembly.NewAssembler(streamPool)

	// Fast Decoding
	parser := gopacket.NewDecodingLayerParser(
		layers.LayerTypeEthernet, &eth, &ip4, &tcp, &payload)
	decoded := make([]gopacket.LayerType, 0, 4)

	nextFlush := time.Now().Add(time.Second)

loop:
	for {

		now := time.Now()
		if now.After(nextFlush) {
			assembler.FlushAll()
			nextFlush = now.Add(intervalDuration)
		}

		data, _, err := handle.ZeroCopyReadPacketData()

		if err != nil {
			log.Printf("error getting packet: %v", err)
			continue
		}

		err = parser.DecodeLayers(data, &decoded)
		if err != nil {
			log.Printf("error decoding packet: %v", err)
			continue
		}

		foundNetLayer := false
		var netFlow gopacket.Flow
		for _, layerType := range decoded {
			switch layerType {
			case layers.LayerTypeIPv4:
				netFlow = ip4.NetworkFlow()
				foundNetLayer = true
			case layers.LayerTypeTCP:
				if foundNetLayer {
					assembler.Assemble(netFlow, &tcp)
				} else {
					log.Println("could not find IPv4 or IPv6 layer, inoring")
				}
				continue loop
			}
		}
	}
}
