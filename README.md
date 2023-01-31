#GerrysGame
A very EPIC app indeed.

BUGS:
- Bug in the Active games list where if you sign out and sign in as a different account, the store value for 'roomId' wont be flushed (which is what gets used to determine by the client which room you're in), so that needs to be cleared on logout and updated on login provided the game is still in play. 

TO DO:
- Add backend room functionality 
  - finish add/remove time to timebank
  - finish add/remove time from clock
  - add admin panel
    - option to adjust interest rates as admin
