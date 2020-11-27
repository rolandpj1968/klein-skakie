import sys
import chess

# From Sunfish
PIECE_VALS = (
    # BLACK
    (
        0, # nothing
        -100, # PAWN
        -280, # KNIGHT
        -320, # BISHOP
        -479, # ROOK
        -929, # QUEEN
        0, # KING
    ),
    (
        0, # nothing
        100, # PAWN
        280, # KNIGHT
        320, # BISHOP
        479, # ROOK
        929, # QUEEN
        0, # KING
    )
)

PIECE_POS_VALS = (
    # BLACK
    (
        # nothing
        (),
        # PAWN
        (   0,   0,   0,   0,   0,   0,   0,   0,
          -78, -83, -86, -73,-102, -82, -85, -90,
           -7, -29, -21, -44, -40, -31, -44,  -7,
           17, -16,   2, -15, -14,   0, -15,  13,
           26,  -3, -10,  -9,  -6,  -1,   0,  23,
           22,  -9,  -5,  11,  10,   2,  -3,  19,
           31,  -8,   7,  37,  36,  14,  -3,  31,
            0,   0,   0,   0,   0,   0,   0,   0),
        # KNIGHT
        (  66,  53,  75,  75,  10,  55,  58,  70,
            3,   6,-100,  36,  -4, -62,   4,  14,
          -10, -67,  -1, -74, -73, -27, -62,   2,
          -24, -24, -45, -37, -33, -41, -25, -17,
            1,  -5, -31, -21, -22, -35,  -2,   0,
           18, -10, -13, -22, -18, -15, -11,  14,
           23,  15,  -2,   0,  -2,   0,  23,  20,
           74,  23,  26,  24,  19,  35,  22,  69),
        # BISHOP
        (  59,  78,  82,  76,  23, 107,  37,  50,
           11, -20, -35,  42,  39, -31,  -2,  22,
            9, -39,  32, -41, -52,  10, -28,  14,
          -25, -17, -20, -34, -26, -25, -15, -10,
          -13, -10, -17, -23, -17, -16,   0,  -7,
          -14, -25, -24, -15,  -8, -25, -20, -15,
          -19, -20, -11,  -6,  -7,  -6, -20, -16,
            7,  -2,  15,  12,  14,  15,  10,  10),
        # ROOK
        ( -35, -29, -33,  -4, -37, -33, -56, -50,
          -55, -29, -56, -67, -55, -62, -34, -60,
          -19, -35, -28, -33, -45, -27, -25, -15,
            0,  -5, -16, -13, -18,   4,   9,   6,
           28,  35,  16,  21,  13,  29,  46,  30,
           42,  28,  42,  25,  25,  35,  26,  46,
           53,  38,  31,  26,  29,  43,  44,  53,
           30,  24,  18,  -5,   2,  18,  31,  32),
        # QUEEN
        (  -6,  -1,   8, 104, -69, -24, -88, -26,
          -14, -32, -60,  10, -20, -76, -57, -24,
            2, -43, -32, -60, -72, -63, -43,  -2,
           -1,  16, -22, -17, -25, -20,  13,   6,
           14,  15,   2,   5,   1,  10,  20,  22,
           30,   6,  13,  11,  16,  11,  16,  27,
           36,  18,   0,  19,  15,  15,  21,  38,
           39,  30,  31,  13,  31,  36,  34,  42),
        # KING
        (  -4, -54, -47,  99,  99, -60, -83,  62,
           32, -10, -55, -56, -56, -55, -10,  -3,
           62, -12,  57, -44,  67, -28, -37,  31,
           55, -50, -11,   4,  19, -13,   0,  49,
           55,  43,  52,  28,  51,  47,   8,  50,
           47,  42,  43,  79,  64,  32,  29,  32,
            4,  -3,  14,  50,  57,  18, -13,  -4,
          -17, -30,   3,  14,  -6,   1, -40, -18),
    ),
    # WHITE
    (
        # nothing
        (),
        # PAWN
        (   0,   0,   0,   0,   0,   0,   0,   0,
          -31,   8,  -7, -37, -36, -14,   3, -31,
          -22,   9,   5, -11, -10,  -2,   3, -19,
          -26,   3,  10,   9,   6,   1,   0, -23,
          -17,  16,  -2,  15,  14,   0,  15, -13,
            7,  29,  21,  44,  40,  31,  44,   7,
           78,  83,  86,  73, 102,  82,  85,  90,
            0,   0,   0,   0,   0,   0,   0,   0),
        # KNIGHT
        ( -74, -23, -26, -24, -19, -35, -22, -69,
          -23, -15,   2,   0,   2,   0, -23, -20,
          -18,  10,  13,  22,  18,  15,  11, -14,
           -1,   5,  31,  21,  22,  35,   2,   0,
           24,  24,  45,  37,  33,  41,  25,  17,
           10,  67,   1,  74,  73,  27,  62,  -2,
           -3,  -6, 100, -36,   4,  62,  -4, -14,
          -66, -53, -75, -75, -10, -55, -58, -70),
        # BISHOP
        (  -7,   2, -15, -12, -14, -15, -10, -10,
           19,  20,  11,   6,   7,   6,  20,  16,
           14,  25,  24,  15,   8,  25,  20,  15,
           13,  10,  17,  23,  17,  16,   0,   7,
           25,  17,  20,  34,  26,  25,  15,  10,
           -9,  39, -32,  41,  52, -10,  28, -14,
          -11,  20,  35, -42, -39,  31,   2, -22,
          -59, -78, -82, -76, -23,-107, -37, -50),
        # ROOK
        ( -30, -24, -18,   5,  -2, -18, -31, -32,
          -53, -38, -31, -26, -29, -43, -44, -53,
          -42, -28, -42, -25, -25, -35, -26, -46,
          -28, -35, -16, -21, -13, -29, -46, -30,
            0,   5,  16,  13,  18,  -4,  -9,  -6,
           19,  35,  28,  33,  45,  27,  25,  15,
           55,  29,  56,  67,  55,  62,  34,  60,
           35,  29,  33,   4,  37,  33,  56,  50),
        # QUEEN
        ( -39, -30, -31, -13, -31, -36, -34, -42,
          -36, -18,   0, -19, -15, -15, -21, -38,
          -30,  -6, -13, -11, -16, -11, -16, -27,
          -14, -15,  -2,  -5,  -1, -10, -20, -22,
            1, -16,  22,  17,  25,  20, -13,  -6,
           -2,  43,  32,  60,  72,  63,  43,   2,
           14,  32,  60, -10,  20,  76,  57,  24,
            6,   1,  -8,-104,  69,  24,  88,  26),
        # KING
        (  17,  30,  -3, -14,   6,  -1,  40,  18,
           -4,   3, -14, -50, -57, -18,  13,   4,
          -47, -42, -43, -79, -64, -32, -29, -32,
          -55, -43, -52, -28, -51, -47,  -8, -50,
          -55,  50,  11,  -4, -19,  13,   0, -49,
          -62,  12, -57,  44, -67,  28,  37, -31,
          -32,  10,  55,  56,  56,  55,  10,   3,
            4,  54,  47, -99, -99,  60,  83, -62),
    )
)


class Game:
    def __init__(self):
        self.board = chess.Board()

    def static_eval(self):
        val = 0
        for color in [chess.BLACK, chess.WHITE]:
            for piece_type in [chess.PAWN,  chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
                sqSet = self.board.pieces(piece_type, color)
                while sqSet != 0:
                    sq = sqSet.pop()
                    val += PIECE_VALS[color][piece_type]
                    val += PIECE_POS_VALS[color][piece_type][sq]
        return val

    def minimax(self, depth):
        if depth == 0:
            val = self.static_eval() * [-1, 1][int(self.board.turn)]
            return None, val, []

        best_move = None
        best_eval = -1000000
        best_rpv = []

        for move in self.board.legal_moves:
            self.board.push(move)
            child_best_move, child_eval, child_rpv = self.minimax(depth-1)
            self.board.pop()

            move_eval = -child_eval
        
            if best_eval < move_eval:
                best_move = move
                best_eval = move_eval
                child_rpv.append(self.board.san(move))
                best_rpv = child_rpv

        return best_move, best_eval, best_rpv
            
    def alphabeta(self, depth, alpha, beta):
        if depth == 0:
            val = self.static_eval() * [-1, 1][int(self.board.turn)]
            return None, val, []

        best_move = None
        best_eval = -1000000
        best_rpv = []

        for move in self.board.legal_moves:
            self.board.push(move)
            child_best_move, child_eval, child_rpv = self.alphabeta(depth-1, -beta, -alpha)
            self.board.pop()

            move_eval = -child_eval

            if beta <= move_eval:
                return None, move_eval, []

            if alpha < move_eval:
                alpha = move_eval
        
            if best_eval < move_eval:
                best_move = move
                best_eval = move_eval
                child_rpv.append(self.board.san(move))
                best_rpv = child_rpv

        return best_move, best_eval, best_rpv
            
    def play(self):
        print_board = True
        while True:
            legal_move_sans = [self.board.san(m) for m in self.board.legal_moves]
            
            print()
            
            if print_board:
                print(self.board)
                print()
            print_board = True

            if self.board.is_game_over():
                print("Game over: %s" % self.board.result())
                print()
                print("Moves: %s" % self.board.move_stack)
                sys.exit()
            
            print("%s to move" % ["Black", "White"][int(self.board.turn)])
            print()
            print("Static eval - positive is White advantage: %d" % self.static_eval())
            print()
            print("Legal moves: %s" % " ".join(legal_move_sans))
            print()
            move_san = input("Enter move - SAN format - or 'pass' or 'engine': ")

            if move_san == "pass":
                # null move - let the other side move
                if self.board.is_check():
                    print()
                    print(">>> Illegal to 'pass' when in check <<<")
                    print_board = False
                    continue
                
                self.board.push(chess.Move.null())
                continue

            if move_san == 'engine':
                print()
                print("Calculating...")
                engine_move, val, rpv = self.minimax(3)
                # engine_move, val, rpv = self.alphabeta(3, -1000000, 1000000)
                pv = rpv[::-1]
                move_san = self.board.san(engine_move)
                print("               ... klein skakie chooses move %s with minimax depth 3 - PV is %s" % (move_san, pv))

            if not move_san in legal_move_sans:
                print()
                print(">>> Illegal move \"%s\" entered <<<" % move_san)
                print_board = False
                continue

            move = self.board.push_san(move_san)

def main():
    print("Hallo RPJ - let's play chess")
    game = Game()
    game.play()
    

if __name__ == "__main__":
    main()
