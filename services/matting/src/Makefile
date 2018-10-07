
all: SharedMatting.cpp
	g++ main.cpp SharedMatting.cpp -o matting -I. `pkg-config --cflags --libs opencv`
install: all
	cp matting /usr/local/bin/
clean:
	rm -rf matting
	