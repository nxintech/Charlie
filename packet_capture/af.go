package main

// http://elixir.free-electrons.com/linux/latest/source/Documentation/networking/packet_mmap.txt
// https://github.com/elastic/beats/blob/master/packetbeat/sniffer/afpacket_linux.go
// http://www.bisrael8191.com/Go-Packet-Sniffer/
// https://github.com/JustinAzoff/can-i-use-afpacket-fanout
// https://github.com/JustinAzoff/gotm/blob/master/main.go

// gopacket/afpacket/header.go:141:103: could not determine kind of name for C.sizeof_struct_tpacket3_hdr
// https://github.com/google/gopacket/issues/149
// yum install kernel-headers

import (
	"fmt"
	"os"
	"log"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/afpacket"
	"github.com/google/gopacket/tcpassembly"
	"time"
)

const (
	buffer_mb int  = 24    // MMap buffer size
	snaplen   int  = 65536 // Max packet length
	promisc   bool = true  // Set the interface in promiscuous mode
)

var (
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

func afpacketComputeSize(target_size_mb int, snaplen int, page_size int) (
	frame_size int, block_size int, num_blocks int, err error) {

	if snaplen < page_size {
		frame_size = page_size / (page_size / snaplen)
	} else {
		frame_size = (snaplen/page_size + 1) * page_size
	}

	// 128 is the default from the gopacket library so just use that
	block_size = frame_size * 128
	num_blocks = (target_size_mb * 1024 * 1024) / block_size

	if num_blocks == 0 {
		return 0, 0, 0, fmt.Errorf("Buffer size too small")
	}

	return frame_size, block_size, num_blocks, nil
}

func NewHandle() (*afpacket.TPacket ,error) {
	frame_size, block_size, num_blocks, err := afpacketComputeSize(
		buffer_mb,
		snaplen,
		os.Getpagesize())
	if err != nil {
		log.Fatalf("Error calculating afpacket size: %s", err)
	}

	tPacket, err := afpacket.NewTPacket(
		afpacket.OptInterface("eth0"),
		afpacket.OptFrameSize(frame_size),
		afpacket.OptBlockSize(block_size),
		afpacket.OptNumBlocks(num_blocks))

	if err != nil {
		log.Fatalf("Error opening afpacket interface: %s", err)
		return nil, err
	}

	return tPacket, nil
}

func main() {

	handle, _ := NewHandle()

	decoded := []gopacket.LayerType{}

	// Faster, predefined layer parser that doesn't make copies of the layer slices
	parser := gopacket.NewDecodingLayerParser(
		layers.LayerTypeEthernet,
		&eth,
		&ip4,
		&tcp,
		&payload)


	// Set up assembly
	streamPool := tcpassembly.NewStreamPool(&streamFactory{})
	assembler := tcpassembly.NewAssembler(streamPool)

	nextFlush := time.Now().Add(time.Second)

loop:
	for {

		now := time.Now()
		if now.After(nextFlush) {
			assembler.FlushAll()
			nextFlush = now.Add(time.Second)
		}


		data, _, err := handle.ZeroCopyReadPacketData()

		err = parser.DecodeLayers(data, &decoded)

		// No decoder for layer type ARP
		parser.IgnoreUnsupported = true
		if err != nil {
			log.Printf("Error decoding packet: %v", err)
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
