import discord
from discord.ext import commands
from codenames.board import Board, CardTypes
import pygame
from codenames.constants import WIDTH, HEIGHT, BLUE_EMOJI, RED_EMOJI, BLUE_TEAM, RED_TEAM
from codenames.teams import Team
from codenames.player import Player


class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.board = Board()
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        self.players = {}
        self.teams = {BLUE_TEAM: Team(BLUE_TEAM, self, BLUE_EMOJI), RED_TEAM: Team(RED_TEAM, self, RED_EMOJI)}
        self.started = False
        self.guessing_team = None
        self.ended = False

    @commands.Cog.listener()
    async def on_ready(self):
        print("Game Cog is online")

    # Checks if the teams have enough players. Returns False if both teams have enough players
    async def teams_need_more_members(self, ctx):
        if len(self.teams[BLUE_TEAM].get_players()) <= 1:
            await ctx.send(" | Blue team doesn't have enough players")
        if len(self.teams[RED_TEAM].get_players()) <= 1:
            await ctx.send(" | Red team doesn't have enough players")
        return len(self.teams[BLUE_TEAM].get_players()) <= 1 or len(self.teams[RED_TEAM].get_players()) <= 1

    # Checks if the teams have spymasters. Returns False if both teams have a spymaster
    async def teams_need_spymasters(self, ctx):
        if not self.teams[BLUE_TEAM].spymaster:
            await ctx.send(" | Blue team doesn't have a spymaster")
        if not self.teams[RED_TEAM].spymaster:
            await ctx.send(" | Red team doesn't have a spymaster")
        return not (self.teams[BLUE_TEAM].spymaster and self.teams[RED_TEAM].spymaster)

    # Checks if the game has started
    async def game_has_started(self, ctx):
        if self.started:
            await ctx.send(" | Game has already started")
        return self.started

    # Check if the author has joined a team
    async def is_not_a_player(self, ctx):
        if ctx.author.id not in self.players:
            await ctx.send(" | Please join a team with !join teamname")

        return ctx.author.id not in self.players

    # Checks if the board has been configured
    async def board_is_not_configured(self, ctx):
        if not self.board.configured:
            await ctx.send(" | Please configure the board using !configure")
        return not self.board.configured

    # Removes your team's spymaster
    async def remove_spymaster(self, ctx):
        if ctx.author.id in self.players and self.players[ctx.author.id].team.spymaster == ctx.author.id:
            team = self.players[ctx.author.id].team
            team.spymaster = None
            await ctx.send(f" {team.emoji} | {team.name} needs a new spymaster!")

    # Displays the GameBoard
    async def display_board(self, ctx):
        self.board.draw_board(self.win)
        pygame.image.save(self.win, "codenames/Board.jpg")
        file = discord.File("codenames/Board.jpg", filename="image.png")
        embed = discord.Embed(
            description=":blue_circle: {} | :red_circle: {}".format(self.board.blue_agents, self.board.red_agents))
        embed.set_image(url="attachment://image.png")
        await ctx.send(file=file, embed=embed)

    # Configures the GameBoard
    @commands.command(name="configure", brief="generates keycard and board")
    async def configure(self, ctx):
        if self.board.configured:
            return

        pygame.font.init()
        self.board.configured = True
        self.board.populate_board()
        await self.display_board(ctx)

    # Allows the user to join a team. If they are the spymaster of their current team, remove them.
    @commands.command(name="join", brief="Allows you to join the blue or red team")
    async def join(self, ctx, colour):
        if await self.game_has_started(ctx):
            return
        if colour.lower() not in [BLUE_TEAM, RED_TEAM]:
            await ctx.send("That is not a valid team!")
        else:
            team = self.teams[colour.lower()]
            await self.remove_spymaster(ctx)
            self.players[ctx.author.id] = Player(ctx.author, team)
            await ctx.send(f" {team.emoji} | Successfully joined the {team.name} team!")

    @join.error
    async def info_error(self, ctx, error):
        print(error)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please include the team colour!')

    # Makes the player a spymaster.
    @commands.command(brief="Assigns the author as the spymaster for their team", name="spymaster")
    async def spymaster(self, ctx):
        if await self.is_not_a_player(ctx):
            return

        # Makes sure the player's team didn't already have a spymaster.
        player_team = self.players[ctx.author.id].team
        if player_team.spymaster:
            await ctx.send("{} team already has a spymaster".format(player_team.name))
        else:
            player_team.spymaster = ctx.author.id
            await ctx.send(" | You are now the spymaster for the {} team".format(player_team.name))

    # Removes the author as the spymaster of their team
    @commands.command(name="unspymaster", brief="Removes the team's spymaster if the player is the spymaster")
    async def unspymaster(self, ctx):
        if await self.game_has_started(ctx):
            return
        await self.remove_spymaster(ctx)

    # Starts the game. Whoever calls this command will allow his team to go first. Any player is allowed to start
    @commands.command(name="start", brief="Starts the game with the author's team going first")
    async def start(self, ctx):
        # Standard checks that need to be done before starting the game
        if await self.game_has_started(ctx) or await self.is_not_a_player(ctx) or await self.board_is_not_configured(ctx) \
                or await self.teams_need_spymasters(ctx) or await self.teams_need_more_members(ctx):
            return

        # Gives the double agent to the starting team, pushing them up to 9 players
        player_team = self.players[ctx.author.id].team.name

        if player_team == BLUE_TEAM:
            self.board.blue_agents = 9
        else:
            self.board.red_agents = 9

        self.guessing_team = player_team

        # Draws the keycard and sends it to the spymasters in a DM
        self.board.generate_keycard(self.guessing_team)
        self.board.draw_keycard(self.win)
        pygame.image.save(self.win, "codenames/Keycard.jpg")

        for team in self.teams.values():
            spymaster = team.spymaster
            file = discord.File("codenames/Keycard.jpg", filename="image.png")
            await self.players[spymaster].user.send(file=file)

        await ctx.send("{} | {} it's your turn".format(self.teams[player_team].emoji, ctx.author.name))
        await self.display_board(ctx)
        self.started = True

    # Allows the spymaster to give his players a hint and the number of words that hint applies to
    @commands.command(name="clue", brief="The spymaster gives his teammates the clue, as well as the number of guesses")
    async def clue(self, ctx, word, num_guesses):
        # Makes sure the game has started and the the author is a player
        if not await self.game_has_started(ctx):
            await ctx.send(" | The Game has not yet started")
            return
        if await self.is_not_a_player(ctx):
            return

        # Makes sure the author is the spymaster of the current team
        current_team = self.teams[self.guessing_team]
        if ctx.author.id != current_team.spymaster:
            await ctx.send("Only the {} spymaster can give clues".format(self.guessing_team))
        else:
            current_team.guesses = int(num_guesses)  # Num_guesses from Discord comes as a string
            await ctx.send(f" {current_team.emoji} | Clue for the {current_team.name} team: {word}({num_guesses})")

    @clue.error
    async def clue_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please include the clue and number of guesses!')

    @commands.command(name="guess", description="A member of the current team sends his guesses.")
    async def guesses(self, ctx, *args):
        if not await self.game_has_started(ctx):
            await ctx.send(" | The Game has not yet started")
            return
        if await self.is_not_a_player(ctx):
            return

        # Makes sure the player is on the right team, is not the spymaster and the correct number of guesses were sent
        if self.players[ctx.author.id].team.name != self.guessing_team:
            await ctx.send(f" | Only {self.guessing_team} players are allowed to guess right now")
        elif ctx.author.id == self.players[ctx.author.id].team.spymaster:
            await ctx.send(f" | The Spymaster is not allowed to guess!")
        elif len(args) > self.teams[self.guessing_team].guesses:
            await ctx.send(f" | You are only allowed {self.teams[self.guessing_team].guesses}")
            await ctx.send(f" | If you entered a multi-word guess, enclose that word in quotes (\" \")")
        else:
            team = self.teams[self.guessing_team]
            # Goes through all of the guesses. It makes sure that they are in the word list, and if they are then the
            # game logic applies. Otherwise, it just skips that word.
            for guess in args:
                if guess.lower() in self.board.word_list:
                    (i, j) = self.board.word_list[guess]

                    # If the players guess a word they already revealed, then do not change the number of guesses
                    # available or the number of agents
                    if self.board.revealed[i][j]:
                        await ctx.send("You already guessed this word")
                        continue

                    # Tells the draw board function to reveal the colour of that square and reduces remaining guesses
                    self.board.revealed[i][j] = True
                    team.guesses -= 1

                    # Picking the correct card is the only one where you don't instantly end your turn.
                    # Therefore, grouped the others under one condition.
                    if self.board.keycard[i][j] == team.card_type:
                        await ctx.send(f" {team.emoji} | {guess} was correct!")
                        if team.name == RED_TEAM:
                            self.board.red_agents -= 1
                        else:
                            self.board.blue_agents -= 1
                    else:
                        # Checks the CardType of the selected square. Assassin instantly ends the game, Bystander
                        # ends the current teams turn, and picking the other team's agent, ends your turn and gives
                        # them a point.
                        if self.board.keycard[i][j] == CardTypes.Assassin:
                            await ctx.send(f" {team.emoji} | You picked the assassin. {team.name} team loses :(")
                            self.ended = True
                        elif self.board.keycard[i][j] == CardTypes.Bystander:
                            await ctx.send(f" {team.emoji} | You picked a bystander. Your turn is over!")
                            self.board.bystanders -= 1
                        else:
                            await ctx.send(f" {team.emoji} | {guess} belonged to the other team. Your turn is over!")
                            # Reduces the number of agents that the other team has to look for
                            if team.name == RED_TEAM:
                                self.board.blue_agents -= 1
                            else:
                                self.board.red_agents -= 1

                        team.guesses = 0  # Otherwise it will think that the current team can still pick again.
                        break
                else:
                    await ctx.send(f" | {guess} is not a valid word.")

            # Displays the board after the current team's guesses
            await self.display_board(ctx)

            # End the game if one of the team has found all of their agents, or if the assassin has been found
            if self.board.red_agents == 0 or self.board.blue_agents == 0 or self.ended:
                if self.board.red_agents == 0:
                    await ctx.send(f"{RED_EMOJI} | Red team has found all of their agents. They win!")
                elif self.board.blue_agents == 0:
                    await ctx.send(f"{BLUE_EMOJI} | Blue team has found all of their agents. They win !")

                await ctx.send("THANKS FOR PLAYING 8==D :sweat_drops:")
                await self.reload()
                return

            # If the current team still has guesses, they can still guess. Otherwise, end their turn.
            if team.guesses > 0:
                await ctx.send(f" {team.emoji} | You still have {team.guesses} guesses!")
            else:
                self.guessing_team = RED_TEAM if self.guessing_team == BLUE_TEAM else BLUE_TEAM
                team = self.teams[self.guessing_team]
                await ctx.send(f"{team.emoji} | {team.name} team it's your turn!")

    # Reload the game cogs so that you can replay the Game
    async def reload(self):
        self.bot.unload_extension(f"cogs.game")
        self.bot.load_extension(f"cogs.game")


def setup(bot):
    bot.add_cog(Game(bot))
