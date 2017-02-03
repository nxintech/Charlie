1 install node


2 install node package
```
npm install bundle pug-cli nodemon reflex less -g
```

3 install go package
```
go get -u github.com/jteeuwen/go-bindata/...
go get github.com/mitchellh/gox
go get github.com/gorilla/websocket
go get github.com/gorilla/securecookie
go get github.com/masterminds/squirrel
go get github.com/google/go-github/github
go get github.com/gin-gonic/gin
go get github.com/russross/blackfriday
go get github.com/masterminds/squirrel
go get gopkg.in/gorp.v1
go get github.com/bugsnag/bugsnag-go
```
'golang.org/x/net/context' need VPN in China use 'github.com/golang' instead of it.
```
cd $GOPATH/src
go get github.com/golang/net
mv github.com/golang/net golang.org/x/net
go get github.com/golang/crypto/bcrypt
mv github.com/golang/crypto golang.org/x/
go get github.com/liuyangc3/semaphore
```

4 compile js css html
```
cd public
rm -rf vendor
git clone https://github.com/ansible-semaphore/semaphore-vendor.git vendor
npm install async
node ./bundler.js
lessc css/semaphore.less > css/semaphore.css
pug html/*.jade html/*/*.jade html/*/*/*.jade
```

5 add a line after `go-bindata` in make.sh
```
cp util/bindata.go $GOPATH/github.com/liuyangc3/semaphore/util/bindata.go
```

6 build
```
./make.sh
```
