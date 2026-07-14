import traceback
from Utils.tools import Tools, CustomException
from Utils.graph_service import GraphService


class Correos:

    def __init__(self, db):
        self.tools = Tools()
        self.db    = db
        self.graph = GraphService.get_instance()

    def listar(self, data: dict):
        page       = int(data.get("page", 1))
        limit      = int(data.get("limit", 20))
        search     = str(data.get("search", "")).strip()
        date_from  = str(data.get("date_from", "")).strip()
        date_to    = str(data.get("date_to", "")).strip()
        sort_order = str(data.get("sort_order", "desc")).strip()

        # leidos: null = todos, true = leídos, false = no leídos
        leidos_raw = data.get("leidos", None)
        leidos = None if leidos_raw is None else bool(leidos_raw)

        try:
            result = self.graph.list_emails(
                self.db,
                page=page, limit=limit, search=search,
                leidos=leidos, date_from=date_from,
                date_to=date_to, sort_order=sort_order,
            )
            return self.tools.output(200, "Correos obtenidos", result)
        except CustomException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error obteniendo correos: {e}", 500)

    def detalle(self, data: dict):
        message_id = str(data.get("id", "")).strip()
        if not message_id:
            raise CustomException("El campo id es requerido.", 400)

        try:
            result = self.graph.get_email_detail(self.db, message_id)
            return self.tools.output(200, "Detalle obtenido", result)
        except CustomException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise CustomException(f"Error obteniendo detalle del correo: {e}", 500)
