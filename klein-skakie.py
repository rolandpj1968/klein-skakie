import sys
import chess

from util import fen4, move_list_to_sans

import evaluate

from engine import Engine

import cProfile

class Game:
    def __init__(self, board = chess.Board()):
        self.board = board
        # TODO - separate engines for Black and White
        # TODO - docs reckon this only copies the base-board - what about previous moves?
        self.engine = Engine(board.copy())

    def play(self):
        print_board = True
        while True:
            legal_move_sans = [self.board.san(m) for m in self.board.legal_moves]
            
            print()
            
            if print_board:
                print(self.board.fen())
                # print()
                # print(self.board)
                print()
                print(self.board.unicode(invert_color=True, empty_square='.')) # Unicode chars seems backwards; Don't seem to have the default empty_square unicode in my font
                print()
            print_board = True

            if self.board.is_game_over():
                
                reason = 'unknown'
                if self.board.is_checkmate():
                    reason = 'checkmate'
                elif self.board.is_stalemate():
                    reason = 'stalemate'
                elif self.board.is_insufficient_material():
                    reason = 'insufficient material'
                elif self.board.is_seventyfive_moves():
                    reason = '75 moves played without progress'
                elif self.board.is_fivefold_repetition():
                    reason = '5-fold repetition'
                    
                print("Game over: %s (%s)" % (self.board.result(), reason))

                print()
                print("Moves: %s" % move_list_to_sans(self.board.root(), self.board.move_stack))
                return
            
            print("%s to move" % ["Black", "White"][self.board.turn])
            print()
            val = self.engine.static_eval()
            print("Static eval - positive is White advantage: %d" % val)
            # qval = self.engine.quiesce_alphabeta(SearchStats(MAX_DEPTH, MAX_QDEPTH), 0, val)
            # print("Quiesced eval - positive is White advantage: %d" % qval)
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
                
                move = chess.Move.null()

            elif move_san == 'engine':
                engine_move, val, pv, stats = self.engine.gen_move()
                
                move = engine_move

            else:
                if not move_san in legal_move_sans:
                    print()
                    print(">>> Illegal move \"%s\" entered <<<" % move_san)
                    print_board = False
                    continue

                move = self.board.parse_san(move_san)
                
            self.board.push(move)
            self.engine.make_move(move)

def main():
    print("Hallo RPJ - let's play chess")
    game = Game()
    game.play()

if __name__ == "__main__":
    main()
    # cProfile.run("main()")

