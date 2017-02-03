```
npm install -g pug-cli
cd public
npm install async
rm -rf vendor
git clone https://github.com/ansible-semaphore/semaphore-vendor.git vendor
```
```
go get github.com/liuyangc3/semaphore
./make.sh  # this will build error
cp util/bindata.go $GOPATH/src/github.com/liuyangc3/semaphore/util/bindata.go
./make.sh
```
