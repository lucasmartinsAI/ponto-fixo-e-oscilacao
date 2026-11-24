import math
import unittest

import simulacao as s


class TestPontoFixo(unittest.TestCase):
    def test_ponto_fixo_exato(self):
        F, pstar = s.modelo(0.7)
        self.assertAlmostEqual(F(pstar), pstar, places=9)          # F(p*) = p*

    def test_razao_entre_passos_e_menos_beta(self):
        traj, _ = s.trajetoria(0.7, 1.0, 6)
        for t in range(2, 6):
            razao = (traj[t] - traj[t - 1]) / (traj[t - 1] - traj[t - 2])
            self.assertAlmostEqual(razao, -0.7, places=9)

    def test_aitken_exato_sem_ruido(self):
        for beta in (0.3, 0.7, 0.9):
            F, pstar = s.modelo(beta)
            self.assertAlmostEqual(s.aitken(s.P0, F(s.P0), F(F(s.P0))), pstar, places=9)

    def test_iteracao_simples_diverge_com_beta_maior_que_1(self):
        self.assertIsNone(s.passos_ate_convergir(1.3, 1.0))

    def test_media_resgata_beta_maior_que_1(self):
        self.assertIsNotNone(s.passos_ate_convergir(1.3, 0.5))

    def test_media_converge_mais_rapido_com_beta_0_7(self):
        self.assertLess(s.passos_ate_convergir(0.7, 0.5), s.passos_ate_convergir(0.7, 1.0))

    def test_reprodutivel(self):
        self.assertEqual(s.experimento_4(repeticoes=200), s.experimento_4(repeticoes=200))


if __name__ == "__main__":
    unittest.main()
