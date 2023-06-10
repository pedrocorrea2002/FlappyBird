import pygame
import os
import random # Necessário para deixar a posição dos canos aleatória
import neat # Pacote que trás a rede neural evolutiva

IA_jogando = True
geracao = 0 #número da geração atual

LARGURA_TELA = 500
ALTURA_TELA = 800

# A função do scale2x é justamente deixar as imagens 2 vezes maiores para não ficarem tão pequenas quando mostradas
CANO_IMAGEM = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','pipe.png')))
CHAO_IMAGEM = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','base.png')))
BACKGROUND_IMAGEM = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bg.png')))
PASSARO_IMAGENS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs','bird3.png')))
]

pygame.font.init() #INICIALIZANDO FONTE
PONTUACAO_FONTE = pygame.font.SysFont('arial',50)


class Passaro:
    IMAGENS = PASSARO_IMAGENS

    # animações da rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    def __init__(self, x,y):
        # x e y são as posições que você vai passar por parâmetro quando for passar o próprio pássro
        # Ex: Passado(20,20)
        # Enquanto self é uma forma de se referir a essa própria classe, é tipo o this do Javascript
        self.x = x
        self.y = y #altura real
        self.angulo = 0 #valor inicial
        self.velocidade = 0 #valor inicial
        self.altura = self.y #altura antes do pulo atual ter iniciado
        self.tempo = 0 #tempo necessário para fazer a parábola do pulo
        self.contagem_imagem = 0 #número da imagem usada em determinado momento
        self.imagem = self.IMAGENS[0] #imagem inicial

    #pássaro sobe
    def pular(self):
        self.velocidade = -15
        self.tempo = 0
        self.altura = self.y

    #passaro desce
    def mergulho(self):
        self.velocidade = 20
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular o deslocamento
        self.tempo += 1
        deslocamento = 1.5 * (self.tempo**2) + self.velocidade * self.tempo # formula de deslocamento : S - So = Vo*t + (a*t²)/2

        # será necessário limitar a altura máxima que o passaro pode chegar só pulando, para evitar que ele saia do mapa
        if deslocamento > 16 :
            deslocamento = 16
        # também será necessário impedir que ele continue caindo infinitamente caso caia
        if deslocamento < 0 :
            deslocamento -= 2 # esse 2 é tipo um incremento para o pulo

        self.y += deslocamento

        # também será necessário controlar o ângulo do passaro, para que a inclinação dele durante a queda seja mais suave, semelhante ao jeito que é no jogo original
        if deslocamento < 0 or self.y < (self.altura + 50) :
            if self.angulo < self.ROTACAO_MAXIMA :
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -90 : # a ideia aqui tambem é evitar que o passado continue girando mesmo após atingir -90 graus
                self.angulo -= self.VELOCIDADE_ROTACAO

    #spawna o passaro
    def desenhar(self, tela):
        # definir qual imagem do passado vai usar
        self.contagem_imagem += 1

        if self.contagem_imagem < self.TEMPO_ANIMACAO: #abaixando a asa
            self.imagem = self.IMAGENS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*2:
            self.imagem = self.IMAGENS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*3:
            self.imagem = self.IMAGENS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*4: #voltando a asa pra cima de novo
            self.imagem = self.IMAGENS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*5: #voltando a asa pra cima de novo
            self.imagem = self.IMAGENS[0]
            self.contagem_imagem = 0

        # se o passaro estiver caindo, ele não vai bater asa
        if self.angulo <= -80:
            self.imagem = self.IMAGENS[1]
            self.contagem_imagem = self.TEMPO_ANIMACAO*2

        # desenhar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        posicao_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=posicao_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft) #desenhando imagem na tela, utilizando o retângulo o canto superior-esquerdo do retângulo como ponto de referência

    # ESSA FUNÇÃO FAZ UMA MASCARA NO RETANGULO DE COLISÃO, DIVIDINDO ELE EM VARIOS QUADRADINHOS DO TAMANHO DE PIXELS, COM ISSO A COLISÃO VAI SER ANALISADA COM BASE NESSES QUADRINHOS E NÃO COM BASE NO RETÂNGULO, FAZENDO COM QUE SÓ SEJA CONSIDERADO COLISÃO SE HOUVER AO MESMO UM PEDAÇO DO CANO E DO PASSARO AO MESMO TEMPO DENTRO DESSE "PIXEL"
    def get_mask(self):
        return pygame.mask.from_surface(self.imagem)
class Cano:
    VELOCIDADE = 5

    def __init__(self, x):
        self.DISTANCIA_ENTRE_CANOS = random.randrange(100, 250)  # distancia entre o cano de baixo e o de cima
        self.x = x
        self.altura = 0 #posição do canto inferior esquerdo do cano superior
        self.pos_topo = 0
        self.pos_base = 0
        self.CANO_TOPO = pygame.transform.flip(CANO_IMAGEM,False, True)
        self.CANO_BASE = CANO_IMAGEM
        self.passou = False # Se o passaro já passou ou não desse caso
        self.definir_altura() #A altura será definida aleatoriamente
        self.descendo = random.randrange(0,1)
        self.velocidade_vertical = random.randrange(0,10)

    def definir_altura(self):
        self.altura = random.randrange(50, 450) # trás um número aleatorio dentro do intervalo 50--450
        self.pos_topo = self.altura - self.CANO_TOPO.get_height() #pega a posição do canto inferior esquerdo
        self.pos_base = self.altura + self.DISTANCIA_ENTRE_CANOS

    def mover(self):
        self.x -= self.VELOCIDADE

        #fazendo os canos se moverem na vertical
        #fazendo ele descer
        if self.altura <= 450 and self.descendo == 1:
            self.altura += self.velocidade_vertical
            self.pos_topo = self.altura - self.CANO_TOPO.get_height()  # pega a posição do canto inferior esquerdo
            self.pos_base = self.altura + self.DISTANCIA_ENTRE_CANOS
        elif self.altura > 450 and self.descendo == 1:
            self.descendo = 0

        #fazendo ele subir
        if self.altura >= 50 and self.descendo == 0:
            self.altura -= self.velocidade_vertical
            self.pos_topo = self.altura - self.CANO_TOPO.get_height()  # pega a posição do canto inferior esquerdo
            self.pos_base = self.altura + self.DISTANCIA_ENTRE_CANOS
        elif self.altura < 50 and self.descendo == 0:
            self.descendo = 1

    def desenhar(self,tela):
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y)) #segundo o youtuber esse os número usados aqui precisar ser inteiros, por isso o uso do round
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))  # segundo o youtuber esse os número usados aqui precisar ser inteiros, por isso o uso do round

        topo_sobreposicao = passaro_mask.overlap(topo_mask,distancia_topo) #overlap retorna True caso ouver sobreposição e False caso não
        base_sobreposicao = passaro_mask.overlap(base_mask,distancia_base)

        if topo_sobreposicao or base_sobreposicao:
            return True
        else:
            return False
class Chao:
    VELOCIDADE = 5
    LARGURA = CHAO_IMAGEM.get_width() # a necessidade dessa largura é para poder fazer a lógica de usar dois chãos para dar a impressão de chão infinito
    IMAGEM = CHAO_IMAGEM

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0: # verificando se o chão1 saiu da tela, se sim ele é movido para trás do chão0
            self.x1 = self.LARGURA
        if self.x2 + self.LARGURA < 0: # verificando se o chão2 saiu da tela, se sim ele é movido para trás do chão0
            self.x2 = self.LARGURA

    def desenhar(self,tela):
        tela.blit(self.IMAGEM, (self.x1,self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))

def desenharTela(tela, passaros, canos, chao, pontos) :
    tela.blit(BACKGROUND_IMAGEM, (0,0))

    for passaro in passaros:
        passaro.desenhar(tela)

    for cano in canos:
        cano.desenhar(tela)

    texto = PONTUACAO_FONTE.render(f"Pontuação: {pontos}",1, (255,255,255)) #ESSE 1 FAZ O TEXTO FICAR REDONDINHO AO INVÉS DE PIXELADO
    tela.blit(texto, (LARGURA_TELA - 10 - texto.get_width(),10))
    chao.desenhar(tela)

    # adicionando texto com o número da geração
    if IA_jogando:
        texto = PONTUACAO_FONTE.render(f"Geração: {geracao}", 1,(255, 255, 255))  # ESSE 1 FAZ O TEXTO FICAR REDONDINHO AO INVÉS DE PIXELADO
        tela.blit(texto, (10,10))

    pygame.display.update()

def main(genomas, config): #por obrigação da biblioteca do NEAT a fitness function precisa receber esses 2 parâmetros, nesse caso a fitness function é a main()
    global geracao
    geracao += 1

    if IA_jogando :
        #criando vários passaros
        # em cada lista, para o mesmo index, as informações se referem ao mesmo indivíduo
        lista_redes = [] #[cerébro] guarda as informações da rede reural de cada pássaro
        lista_genomas = [] #[genes responsáveis pelo cérebro] guarda as configurações da rede neural de cada passáro(valor do fitness, número de nós, valor do bias, função de agregação usada atualmente, função de ativação usada atualmente, peso de cada nó, valor de resposta)
        passaros = []

        for _, genoma in genomas: #cada item de genomas é uma tupla com dois valores (idGenoma,genoma), aqui é ignorado o idGenora e usado o genoma
            rede = neat.nn.FeedForwardNetwork.create(genoma,config)
            lista_redes.append(rede)

            # a rede neural vai sempre buscar o caminho que otimize o fitness, se baseando sempre no fitness_criterion definido na configurações
            genoma.fitness = 0 #pontuação inicial de cada pássaro na qual o neat vai se basear, essa pontuação não necessariamente precisa ser a baseada apenas na pontuação do jogo em si, que favoreceria os pássaros que chegam mais longe, existem outras formas de medir a eficiencia fora isso, o que pode deixar o treinamento mais completo
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))
    else :
        passaros = [Passaro(230,350)]
    chao = Chao(730)
    canos = [Cano(700)]
    tela = pygame.display.set_mode((LARGURA_TELA,ALTURA_TELA))
    pontuacao = 0
    relogio = pygame.time.Clock() #Esse relatório serve para definir a cada quanto tempo determina ação será executada
    rodando = True

    while rodando:
        relogio.tick(30) #Esse 30 são os frames por segundo

        # interacao com o usuário
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not IA_jogando:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()

        # fazendo com que o passarp sempre se baseei no cano que está na frente e nunca no cano que está atrás
        indice_cano = 0
        if len(passaros) > 0:
            #vale lembrar que por enquanto o x de todos os passaros é sempre o mesmo
            # se existem dois canos na tela e o passaro já passou do primeiro, olhe o segundo
            if len(canos) > 1 and passaros[0].x > (canos[0].x + canos[0].CANO_TOPO.get_width()) :
                indice_cano = 1
        else:
            rodando = False
            break

        # mover as coisas
        for i, passaro in enumerate(passaros):
            passaro.mover()
            #aumentar um pouquinho a fitness do pássaro
            #quando o pássaro deve pular?
            lista_genomas[i].fitness += 0.1

            #caso o segundo cano já estiver na tela é possível o pássaro planejar como ele vai passar pelo primeiro, dependendo da posição do segundo
            if (len(canos) - 1) > indice_cano :
                # esse activate recebe uma tupla com os inputs
                # o abs é usado porque as redes neurais funcionam muito melhor com números positivos
                output = lista_redes[i].activate((
                    passaro.y,
                    abs(passaro.y - canos[indice_cano].altura),
                    abs(passaro.y - canos[indice_cano].pos_base),
                    abs(passaro.y - canos[indice_cano + 1].altura),
                    abs(passaro.y - canos[indice_cano + 1].pos_base),
                    canos[indice_cano].velocidade_vertical,
                    canos[indice_cano + 1].velocidade_vertical
                ))
            else :
                output = lista_redes[i].activate((
                    passaro.y,
                    abs(passaro.y - canos[indice_cano].altura),
                    abs(passaro.y - canos[indice_cano].pos_base),
                    0,
                    0,
                    canos[indice_cano].velocidade_vertical,
                    0
                ))

            # esse output fica entre -1 e 1 graças a tanH que diminui matrizes para só terem entre -1 e 1 de Y
            if output[0] > 0.5 :
                passaro.pular()

            if output[1] > 0.5 :
                passaro.mergulho()
        chao.mover()

        adicionar_cano = False
        canos_para_excluir = [] #segundo o youtuber, pode dar um problema se os canos forem apagados dentro do for

        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):
                    passaros.pop(i)
                    lista_genomas[i].fitness -= 1 #tirando ponto do passaro que bater no cano
                    lista_genomas.pop(i) #embora eu esteja tirando esse genoma, a IA ainda levará ele em conta na hora de avaliar qual genoma se saiu melhor
                    lista_redes.pop(i)

                if not cano.passou and passaro.x > cano.x - 150:
                    cano.passou = True
                    adicionar_cano = True
            cano.mover()

            #verificando se aquela dupla de canos já sairam da tela para poder apagar eles
            if cano.x + cano.CANO_TOPO.get_width() < 0:
                canos_para_excluir.append(cano)

        if adicionar_cano:
            pontuacao += 1
            canos.append(Cano(600)) #O primeiro cano aparece mais atrás para o usuário que deu Start ter tempo de se situar, agora para os próximos esse tempo extra não é necessário, já que o usuário já está jogando

            for genoma in lista_genomas:
                genoma.fitness += 5 #recomensando todos os pássaros que ainda estão vivos a cada vez que passa um novo cano
        for cano in canos_para_excluir:
            canos.remove(cano)

        # "matando" o passaro caso ele colidir com o teto ou com o chão
        for i, passaro in enumerate(passaros):
            if(passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y < 0:
                passaros.pop(i)

                if IA_jogando:
                    lista_redes.pop(i)
                    #lista_genomas[i].fitness -= 1
                    lista_genomas.pop(i)

        desenharTela(tela,passaros,canos,chao,pontuacao)

def rodar(caminho_config):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        caminho_config
    )

    populacao = neat.Population(config) #criando a população de pássaros

    #trazendo estatísticas sobre o treinamento, para o resultado ser acompanhado no terminal
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter()) #trás informações sobre os genomas e espécies durante cada geração

    if IA_jogando:
        populacao.run(main,50) #fitness_function, ?número máximo de gerações
    else:
        main(None,None)

# a função disso é evitar que o main() seja executado caso esse arquivo esteja sendo importado dentro de outro arquivo
if __name__ == '__main__':
    caminho = os.path.dirname(__file__) #pegando o caminho da pasta onde está este arquivo "flappyBird.py"
    caminho_config = os.path.join(caminho,"neat_configuration.txt")
    rodar(caminho_config)