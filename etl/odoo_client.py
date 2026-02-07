"""
Cliente XML-RPC para conectarse a Odoo.sh.

Usa la API estándar de Odoo:
  - /xmlrpc/2/common  →  autenticación
  - /xmlrpc/2/object  →  operaciones CRUD
"""

import logging
import xmlrpc.client

from config.settings import ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD

logger = logging.getLogger(__name__)


class OdooClient:
    """Wrapper sobre XML-RPC de Odoo con autenticación y lectura por lotes."""

    def __init__(self):
        self.url = ODOO_URL.rstrip("/")
        self.db = ODOO_DB
        self.username = ODOO_USER
        self.password = ODOO_PASSWORD
        self.uid = None
        self._object = None

    def connect(self):
        """Autenticar contra Odoo y almacenar uid."""
        common_url = f"{self.url}/xmlrpc/2/common"
        logger.info("Conectando a Odoo: %s (db=%s, user=%s)", self.url, self.db, self.username)

        common = xmlrpc.client.ServerProxy(common_url, allow_none=True)
        self.uid = common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise ConnectionError(
                f"No se pudo autenticar en Odoo ({self.url}). "
                "Verificar URL, DB, usuario y contraseña/API key."
            )

        self._object = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )
        logger.info("Autenticación exitosa, uid=%s", self.uid)
        return self.uid

    def _execute(self, model, method, *args, **kwargs):
        """Llamada genérica a execute_kw."""
        if self._object is None:
            self.connect()
        return self._object.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs,
        )

    def search_count(self, model, domain=None):
        """Cuenta registros que coinciden con el dominio."""
        return self._execute(model, "search_count", domain or [])

    def search_read(self, model, domain=None, fields=None,
                    offset=0, limit=None, order=None):
        """Lee registros con dominio y campos específicos."""
        opts = {}
        if fields:
            opts["fields"] = fields
        if offset:
            opts["offset"] = offset
        if limit:
            opts["limit"] = limit
        if order:
            opts["order"] = order
        return self._execute(model, "search_read", domain or [], **opts)

    def read_batched(self, model, domain=None, fields=None,
                     batch_size=500, order="id asc"):
        """
        Generador que lee registros en lotes para no saturar la memoria
        ni el timeout de XML-RPC.
        """
        offset = 0
        total = self.search_count(model, domain)
        logger.info("Modelo %s: %d registros a leer (lotes de %d)", model, total, batch_size)

        while offset < total:
            batch = self.search_read(
                model,
                domain=domain,
                fields=fields,
                offset=offset,
                limit=batch_size,
                order=order,
            )
            if not batch:
                break
            yield batch
            offset += len(batch)
            logger.debug("  → %s: leídos %d / %d", model, min(offset, total), total)

    def check_model_exists(self, model):
        """Verifica si un modelo existe en la instancia de Odoo."""
        try:
            self._execute(model, "search_count", [])
            return True
        except xmlrpc.client.Fault:
            return False

    def get_model_fields(self, model):
        """Retorna los campos disponibles de un modelo (útil para debug)."""
        return self._execute(model, "fields_get", [], attributes=["string", "type", "required"])
