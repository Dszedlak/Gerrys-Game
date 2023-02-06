#GerrysGame
A very EPIC app indeed.

BUGS:
- Bug in the Active games list where if you sign out and sign in as a different account, the store value for 'roomId' wont be flushed (which is what gets used by the client to determine which room you're in), so that needs to be cleared on logout and updated on login provided the game is still in play. 

TO DO:
- Add backend room functionality
  - add admin panel
    + option to adjust interest rates as admin
  - remove room (only 1 room per user can be made, and currently only by admins... ?) 
  - changes to interest rates, currently you have -08 etc. Round this up to the nearest 10.
