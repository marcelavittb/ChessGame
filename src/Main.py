import pygame
import sys
from const import *
from game import Game
from square import Square
from move import Move

class Main:
    """
    Classe principal que gerencia o fluxo de execução do jogo de xadrez em pygame.
    """

    def __init__(self):
        """
        Inicializa o pygame, a tela e o objeto do jogo.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.game = Game()

    def _blit_all(self):
        """
        Função auxiliar para redesenhar todos os elementos do jogo na tela.
        """
        self.game.show_bg(self.screen)
        self.game.show_last_move(self.screen)
        self.game.show_moves(self.screen)
        self.game.show_pieces(self.screen)
        self.game.show_hover(self.screen)
        if self.game.dragger.dragging:
            self.game.dragger.update_blit(self.screen)
        
        # Mostra a tela de fim de jogo se o jogo tiver terminado
        if self.game.game_over:
            self.show_game_over()
        
        pygame.display.update()

    def show_game_over(self):
        """
        Exibe a mensagem de fim de jogo na tela.
        """
        font = pygame.font.SysFont('monospace', 50, bold=True)
        if self.game.winner:
            text = f'Xeque-mate! {self.game.winner.capitalize()} venceu!'
        else:
            text = 'Empate por afogamento!'
        
        lbl = font.render(text, True, (255, 0, 0))
        rect = lbl.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(lbl, rect)

    def mainloop(self):
        screen = self.screen
        game = self.game
        dragger = game.dragger

        while True:
            # 1. Desenha todos os elementos do jogo
            self.game.show_bg(screen)
            self.game.show_last_move(screen)
            self.game.show_moves(screen)
            self.game.show_pieces(screen)
            self.game.show_hover(screen)
            if dragger.dragging:
                dragger.update_blit(screen)

            # 2. Lógica da IA (se for a vez dela e o jogo não tiver acabado)
            if not game.game_over and game.next_player == 'black':
                game.ai_move()

            # 3. Processamento de eventos do usuário
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # 4. Lógica do jogador humano (somente se for a vez dele)
                if not game.game_over and game.next_player == 'white':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        dragger.update_mouse(event.pos)
                        row, col = dragger.mouseY // SQSIZE, dragger.mouseX // SQSIZE
                        
                        if game.board.squares[row][col].has_piece():
                            piece = game.board.squares[row][col].piece
                            if piece.color == game.next_player:
                                game.board.calc_moves(piece, row, col)
                                dragger.save_initial(event.pos)
                                dragger.drag_piece(piece)
                    
                    elif event.type == pygame.MOUSEMOTION:
                        row, col = event.pos[1] // SQSIZE, event.pos[0] // SQSIZE
                        game.set_hover(row, col)
                        if dragger.dragging:
                            dragger.update_mouse(event.pos)

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if dragger.dragging:
                            dragger.update_mouse(event.pos)
                            row, col = dragger.mouseY // SQSIZE, dragger.mouseX // SQSIZE
                            
                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(row, col)
                            move = Move(initial, final)

                            if game.board.valid_move(dragger.piece, move):
                                game.play_move(dragger.piece, move)
                            
                        dragger.undrag_piece()

                # 5. Eventos de teclado
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    elif event.key == pygame.K_r:
                        game.reset()

            # 6. Exibe a tela de fim de jogo se a condição for verdadeira
            if game.game_over:
                self.show_game_over()
            
            # Atualiza a tela
            pygame.display.update()

if __name__ == '__main__':
    Main().mainloop()