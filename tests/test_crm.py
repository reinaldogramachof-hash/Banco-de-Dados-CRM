import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server


class CRMIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.temp_dir.name) / "test.db"
        server.initialize_database()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_port}/api"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        login = cls.request("POST", "/auth/login", {"email": "joao@crm.local", "senha": "Senha@123"})
        cls.token = login["token"]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        cls.temp_dir.cleanup()

    @classmethod
    def request(cls, method, path, body=None, authenticated=True):
        headers = {"Content-Type": "application/json"}
        if authenticated and getattr(cls, "token", None):
            headers["Authorization"] = f"Bearer {cls.token}"
        request = Request(
            cls.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request) as response:
                return json.loads(response.read().decode())
        except HTTPError as error:
            payload = json.loads(error.read().decode())
            raise AssertionError(f"{method} {path}: {error.code} - {payload}") from error

    def test_complete_crm_flow(self):
        users = self.request("GET", "/usuarios")
        seller = next(user for user in users if user["email"] == "carlos@crm.local")

        client = self.request("POST", "/clientes", {
            "tipo": "PJ", "nome": "Cliente Teste Integrado", "cpf_cnpj": "99.999.999/0001-99",
            "telefone": "(11) 99999-9999", "email": "cliente@teste.local",
            "segmento": "Tecnologia", "status": "ATIVO",
        })
        updated_client = self.request("PUT", f"/clientes/{client['id']}", {"segmento": "Industria"})
        self.assertEqual(updated_client["segmento"], "Industria")

        lead = self.request("POST", "/leads", {
            "nome": "Lead Integrado", "empresa": "Empresa Lead", "email": "lead.integrado@teste.local",
            "origem": "Google", "status": "QUALIFICADO", "responsavel_id": seller["id"],
        })
        conversion = self.request("POST", f"/leads/{lead['id']}/converter", {
            "cpf_cnpj": "88.888.888/0001-88", "segmento": "Saude", "valor_estimado": 25000,
        })
        opportunity = self.request("GET", f"/oportunidades/{conversion['oportunidade_id']}")
        self.assertEqual(opportunity["valor_estimado"], 25000)

        proposal = self.request("POST", "/propostas", {
            "oportunidade_id": opportunity["id"], "valor": 24000,
            "validade": "2030-12-31", "status": "ENVIADA",
        })
        contract = self.request("POST", f"/propostas/{proposal['id']}/aprovar", {})
        self.assertEqual(contract["status"], "ATIVO")
        self.assertTrue(contract["numero"].startswith("CTR-"))

        receivable = self.request("POST", "/contas-receber", {
            "cliente_id": conversion["cliente_id"], "contrato_id": contract["id"],
            "valor": 24000, "vencimento": "2030-12-31", "status": "ABERTO",
        })
        paid = self.request("POST", f"/contas-receber/{receivable['id']}/baixar", {})
        self.assertEqual(paid["status"], "PAGO")
        self.assertTrue(paid["pagamento"])

        commission = self.request("POST", f"/comissoes/gerar/{contract['id']}", {"percentual": 5})
        self.assertEqual(commission["valor"], 1200)

        dashboard = self.request("GET", "/dashboard/kpis")
        self.assertGreaterEqual(dashboard["clientes_ativos"], 21)
        self.assertIn("financeiro", dashboard)
        self.assertGreater(dashboard["financeiro"]["pago"], 0)

        logs = self.request("GET", "/logs")
        actions = {log["acao"] for log in logs}
        self.assertTrue({"LOGIN", "CREATE", "UPDATE", "STATUS_CHANGE"}.issubset(actions))

        self.request("DELETE", f"/clientes/{client['id']}")


if __name__ == "__main__":
    unittest.main()
