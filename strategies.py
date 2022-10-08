"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

from chess.engine import PlayResult
import random
import math
from engine_wrapper import EngineWrapper


class FillerEngine:
    """
    Not meant to be an actual engine.

    This is only used to provide the property "self.engine"
    in "MinimalEngine" which extends "EngineWrapper"
    """
    def __init__(self, main_engine, name=None):
        self.id = {
            "name": name
        }
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """
    def __init__(self, commands, options, stderr, draw_or_resign, name=None, **popen_args):
        super().__init__(options, draw_or_resign)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {
            "name": self.engine_name
        }

    def search(self, board, time_limit, ponder, draw_offered):
        """
        The method to be implemented in your homemade engine

        NOTE: This method must return an instance of "chess.engine.PlayResult"
        """
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self>
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass


class ExampleEngine(MinimalEngine):
    pass


# Strategy names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    def search(self, board, *args):
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Gets the first move when sorted by uci representation"""
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return PlayResult(moves[0], None)


class AlphaBetaPruning(ExampleEngine):
    piece_values = {
        "p" : -1,
        "P" : 1,
        "r" : -5,
        "R" : 5,
        "n" : -3,
        "N" : 3,
        "b" : -3,
        "B" : 3,
        "q" : -9,
        "Q" : 9
    }

    def search(self, board, *args):

        return PlayResult(self.alphabeta_search(board, 4, board.turn == chess.WHITE, -math.inf, math.inf)[0], None)

    def evaluate_position(self, board):

        if(board.outcome() == None):
            fen_string = board.board_fen()
            eval = 0

            for char in fen_string:
                eval += self.piece_values[char] if char in self.piece_values else 0

            return eval
        
        else:
            result = board.outcome().result()

            if(result == "1-0"):
                #print("Win for white")
                return 300
                
            elif(result == "0-1"):
                return -300

            else:
                return 0


    # Performs a minimax search with alpha/beta pruning and returns best move, along with the evaluation

    def alphabeta_search(self, board, depth, white_to_move, alpha, beta):

        #moves_list = list(board.legal_moves)

        if(depth == 0 or board.is_game_over()):
            eval = self.quiescence_search(board, white_to_move, alpha, beta, 3)[1]
            #eval = evaluate_position(board)
            return (None,eval)

        else:      
            moves_list = self.move_ordering_sort(board, only_captures=False)
            random.shuffle(moves_list)
            
            best_eval = -math.inf if white_to_move else math.inf
            best_move = ''
            global total_branches_pruned

            if(white_to_move):               
                for move in moves_list:
                    # Evaluate each move and recursively find the best one

                    board.push(move)
                    current_eval = self.alphabeta_search(board, depth - 1, False, alpha, beta)[1]  
                    if(current_eval > best_eval):
                        best_eval = current_eval
                        best_move = move

                    board.pop()

                    alpha = max(alpha, current_eval)

                    #if(alpha > 100): print(depth, move, alpha, beta)

                    if(alpha >= beta):

                        total_branches_pruned += 1
                        break


            else:
                for move in moves_list:
                    # Evaluate each move and recursively find the best one

                    board.push(move)
                    current_eval = self.alphabeta_search(board, depth - 1, True, alpha, beta)[1]  
                    if(current_eval < best_eval):
                        best_eval = current_eval
                        best_move = move

                    board.pop()

                    beta = min(beta, current_eval)

                    if(alpha >= beta): 
                        break

            #print(depth, "Best move is: " + str(best_move), "Eval: " + str(best_eval), end=" ")
            return (best_move, best_eval)



    def quiescence_search(self, board, white_to_move, alpha, beta, depth):


        # Very similar to alpha beta - but we only look at captures and checkmates - to solve the horizon issue without huge branching

        moves_list = self.move_ordering_sort(board, only_captures=True)

        #static_eval = evaluate_position(board)

        # if(white_to_move and beta <= static_eval):
        #     return (None, static_eval)

        # elif((not white_to_move) and alpha >= static_eval):
        #     return (None, static_eval)

        #print(moves_list)

        #moves_list = list(board.legal_moves)

        if(board.is_game_over() or moves_list == [] or depth == 0):
            eval = self.evaluate_position(board)
            global total_quiescence_positions_evaluated
            total_quiescence_positions_evaluated += 1
            return (None,eval)

        else:
            #random.shuffle(moves_list)
            best_eval = -math.inf if white_to_move else math.inf
            best_move = ''
            global total_branches_pruned

            if(white_to_move):               
                for move in moves_list:
                    # Evaluate each move and recursively find the best one

                    board.push(move)
                    current_eval = self.quiescence_search(board, False, alpha, beta, depth - 1)[1]  
                    if(current_eval > best_eval):
                        best_eval = current_eval
                        best_move = move

                    board.pop()

                    alpha = max(alpha, current_eval)

                    #if(alpha > 100): print(depth, move, alpha, beta)

                    if(alpha >= beta):

                        total_branches_pruned += 1
                        break


            else:
                for move in moves_list:
                    # Evaluate each move and recursively find the best one

                    board.push(move)
                    current_eval = self.quiescence_search(board, True, alpha, beta, depth - 1)[1]  
                    if(current_eval < best_eval):
                        best_eval = current_eval
                        best_move = move

                    board.pop()

                    beta = min(beta, current_eval)

                    if(alpha >= beta):

                        total_branches_pruned += 1
                        break

            #print(depth, "Best move is: " + str(best_move), "Eval: " + str(best_eval), end=" ")
            return (best_move, best_eval)




    def move_ordering_sort(board, only_captures = False):

        moves_list = list(board.legal_moves)

        captures = []
        #checks = []
        temp_list = []

        for move in moves_list:
            if(board.is_capture(move)):
                captures.append(move)

            # elif(board.gives_check(move)):
            #     checks.append(move)

            else:
                temp_list.append(move)

        if(only_captures):
            return captures

        else:
            return captures + temp_list