## What's this for ? 
Previous Logitech G hub versions used to break a lot on my computer for some undiagnosed reason on my end such as the boot loop, this quick cleaning script helped some times.

It iterates through every directory known to be used by G HUB checks for file locks using sysinternals **handle64** (which is already included but might need to be swapped later).


![Le skreept](https://github.com/Redrrx/LogitechGhubCleaner/blob/master/res/console.png?raw=true)

## Issues
* Not all handlers can be cleared from locked files 100%
* Could overload hardware in some instances if there's too many files.
* False positive in the release executable.

## Warranty
None, this deletes things related with G HUB use at your own RISK!


