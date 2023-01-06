#GerrysGame
A very EPIC app indeed.

Features to be implemented:
- add multithreading functionality, currently only one thread can be open at the same time. Figures this needs to be implemented in a way that a threading class (which has an array of pointers to threads) calls the game session and THERE it invokes a new thread within the threading class. Currently its done within the 'game-session' class. But I believe the issue im having is that once I create an instance of game session, it gets stuck within the context of the thread and fails to go back to the main socketio thread.

- Add backend room functionality 
	- add/remove time to timebank
	- add/remove time from clock
	- add admin panel for interest rates 
