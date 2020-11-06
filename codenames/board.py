import pygame
import enum
from .constants import BLACK, ROWS, COLS, SQUARE_SIZE, RED, BLUE, WHITE, GREY, LIGHT_GREY, BLUE_TEAM, RED_TEAM
import random


class CardTypes(enum.Enum):
    Red = "red agent"
    Blue = "blue agent"
    Bystander = "bystander"
    Assassin = "assassin"


def draw_border(x, y, win):
    for i in range(4):
        pygame.draw.rect(win, BLACK, ((x - i) * SQUARE_SIZE, (y - i) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 1)


class Board:
    def __init__(self):
        self.board = [[""] * COLS for _ in range(ROWS)]
        self.configured = False
        self.blue_agents = self.red_agents = 8
        self.bystanders = 7
        self.keycard = [[CardTypes.Red] * COLS for _ in range(ROWS)]
        self.revealed = [[False] * COLS for _ in range(ROWS)]
        self.type_to_color = {CardTypes.Red: RED, CardTypes.Blue: BLUE, CardTypes.Assassin: GREY,
                              CardTypes.Bystander: WHITE}
        self.word_list = {}

    # Shuffles the list of numbers that represent the cardtypes. Assigns the card types to the keycard using the
    # shuffled order.
    def generate_keycard(self, starting_team):
        team_number = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 4, 4, 4]
        team_to_type = {1: CardTypes.Red, 2: CardTypes.Blue, 3: CardTypes.Assassin, 4: CardTypes.Bystander}

        # If blue is going first, then give them 9 agents. Otherwise, leave red with 9 agents.
        if starting_team == BLUE_TEAM:
            team_to_type[1] = CardTypes.Blue
            team_to_type[2] = CardTypes.Red

        random.shuffle(team_number)

        for i in range(ROWS):
            for j in range(COLS):
                num = team_number[(i * ROWS) + j]
                self.keycard[i][j] = team_to_type[num]

    # Draws the keycard.
    def draw_keycard(self, win):
        for row in range(ROWS):
            for col in range(COLS):
                colour = self.type_to_color[self.keycard[row][col]]
                pygame.draw.rect(win, colour, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 0)
                draw_border(row, col, win)

    # Chooses 25 random words from the codenames_wordlist. It assigns these to the board.
    def populate_board(self):
        with open("codenames/codenames_wordlist.txt", "r") as file:
            word_list = file.readlines()

        game_word_list = random.sample(word_list, 25)
        for i in range(ROWS):
            for j in range(COLS):
                self.board[i][j] = game_word_list[(i * ROWS) + j].rstrip("\n")
                # Keeps track of where the words are. Stores them in lowercase for user convenience without messing up
                # the image of the board.
                self.word_list[self.board[i][j].lower()] = (i, j)

    # Draws the board in its current state. If a word has been revealed it adds the colour of that cell from the keycard
    def draw_board(self, win):
        win.fill(LIGHT_GREY)
        fnt = pygame.font.SysFont("comicsans", 20)

        for row in range(ROWS):
            for col in range(COLS):
                if self.revealed[row][col]:
                    colour = self.type_to_color[self.keycard[row][col]]
                    pygame.draw.rect(win, colour, (row * SQUARE_SIZE, col * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 0)

                text = fnt.render(self.board[row][col], True, BLACK)
                win.blit(text, (row * SQUARE_SIZE + 5, col * SQUARE_SIZE + 50))
                draw_border(row, col, win)
