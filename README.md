# LOL_5v5_Tool
A 5v5 Tool for League of Legends.
This tool currently functions as a demo project combining python with flask and selenium to gather player data and run a simple algorithm I created to generate two evenly matched teams.
Currently, this tool works by scraping the op.ggs of the inputted players (or loading player information stored in json format) which can then be edited in the web portal using html
To run the program simply download the repo and either run Main in an IDE of your choice or open the /dist folder and click main.exe
- Upon executing either option the code will begin scraping player_data
- As a simple example, it will only scrape one player's information instead of 10 as the other 9 are pre-stored on known_players.exe
- Feel free to edit the links in player links, but they must be valid op.gg links (currently only supports NA)
- When scraping, a chrome browser will pop up displaying what the selenium driver is doing; each player takes 15-30 seconds to scrape. (NOTE: you must have chrome installed for this to work)
- (Feel free to use the "full_known_players.json" by changing the name to "known_players.json" and the name of the other file if you want to avoid any scraping; additionally, feel free to delete all 10 links and add new ones to see extended scraping!
- Once the scraping step is done, the Flask app will open at 27.0.0.1:5000; simply type this into any browser and the player information will pop up!
- Feel free to play around with player roles, ranks, and chances then press the update_players button to store that information on the local instance and permanently into known_players.json!
- Press, the make teams button to show an example of a potential balanced team made from the players. You can also view the differences in lanes calculated with my algorithm after ranking all players through gatehred data and/or player entered data
- Feel free to do back to the index/home page by clicking the link at the bottom of the screen or the back button in your browser; each time you click the make teams button, it should be different! (Some combination are deterministic but not most!)
- The more closely ranked the players and spread the roles, the more even the game will be!
- Finally, when you are done simply enter 27.0.0.1:5000/stopServer into your browser to end the program; feel free to end it via task manager instead if you like


Future updates to this project are planned including: The ability to enter more than 10 players, graphic displays of player data, a drafting tool, and more!
