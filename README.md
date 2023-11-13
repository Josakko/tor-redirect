# tor-redirect
Script for redirecting all traffic through tor



## Installation

For debain (and other distros using apt) download `tor-redirect.deb` [here](https://github.com/Josakko/tor-redirect/releases) and also install tor:

```sh
sudo apt install ./tor-redirect.deb tor
```
For non apt distros download tor-redirect executable [here](https://github.com/Josakko/tor-redirect/releases) and for example put it into `/usr/bin/`:

```sh
sudo cp ./Downloads/tor-redirect /usr/bin/tor-redirect
```

## Usage

###### Help

```sh
$ sudo tor-redirect --help

    tor-redirect [arg]

    arguments:

    status              Check if tor-redirect is running already
    start               Start redirecting traffic
    stop                Stop redirecting traffic
    switch              Switch exit node
    --help, -h          Print this message

```

###### Start

```sh
$ sudo tor-redirect start
```

###### Stop

```sh
$ sudo tor-redirect stop
```

## Need Help?
If you need help contact me on my [discord server](https://discord.gg/xgET5epJE6).

## Contributors
Big thanks to all of the amazing people (only me) who have helped by contributing to this project!
