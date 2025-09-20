from dataclasses import dataclass
from typing import List, Optional
import datetime

import db_manager

@dataclass
class GastoFijo:
    id: int
    usuario_id: int
    categoria: str
    monto: float

@dataclass
class GastoVariable:
    id: int
    usuario_id: int
    categoria: str
    monto: float
    fecha: str

class Usuario:
    def __init__(self, id: int, nombre: str, ingreso: float, ahorro_porcentaje: float):
        self.id = id
        self.nombre = nombre
        self.ingreso = float(ingreso)
        self.ahorro_porcentaje = float(ahorro_porcentaje)

    @classmethod
    def create(cls, nombre: str, ingreso: float, ahorro_porcentaje: float) -> "Usuario":
        uid = db_manager.insert_usuario_return_id(nombre, ingreso, ahorro_porcentaje)
        return cls(uid, nombre, ingreso, ahorro_porcentaje)

    @classmethod
    def from_db(cls, usuario_id: int) -> Optional["Usuario"]:
        row = db_manager.get_usuario(usuario_id)
        if not row:
            return None
        return cls(row[0], row[1], row[2], row[3])

    def calcular_ahorro(self) -> float:
        return round(self.ingreso * (self.ahorro_porcentaje / 100.0), 2)

    def gastos_fijos_totales(self) -> float:
        return round(db_manager.total_gastos_fijos(self.id), 2)

    def gastos_variables_totales(self) -> float:
        return round(db_manager.total_gastos_variables(self.id), 2)

    def presupuesto_disponible(self) -> float:
        """
        Presupuesto real disponible considerando ahorro, gastos fijos y variables.
        """
        ahorro = self.calcular_ahorro()
        gastos_fijos = self.gastos_fijos_totales()
        gastos_variables = self.gastos_variables_totales()
        return round(self.ingreso - ahorro - gastos_fijos - gastos_variables, 2)

    def compromiso_total(self) -> float:
        """
        Total comprometido = ahorro + gastos fijos + gastos variables.
        """
        return round(self.calcular_ahorro() + self.gastos_fijos_totales() + self.gastos_variables_totales(), 2)

    def agregar_gasto_fijo(self, categoria: str, monto: float):
        db_manager.insert_gasto_fijo(self.id, categoria, monto)

    def agregar_gasto_variable(self, categoria: str, monto: float, fecha: str = None):
        if fecha is None:
            fecha = datetime.date.today().isoformat()
        db_manager.insert_gasto_variable(self.id, categoria, monto, fecha)

    def listar_gastos_fijos(self) -> List[GastoFijo]:
        rows = db_manager.get_gastos_fijos(self.id)
        return [GastoFijo(*r) for r in rows]

    def listar_gastos_variables(self) -> List[GastoVariable]:
        rows = db_manager.get_gastos_variables(self.id)
        return [GastoVariable(*r) for r in rows]