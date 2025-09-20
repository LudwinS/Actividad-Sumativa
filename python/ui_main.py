from PyQt5 import QtWidgets, QtCore
import sys
import db_manager
from clases import Usuario
import datetime

# categorías definidas
CATEGORIES = ["Alquiler", "Comida", "Transporte", "Servicios", "Entretenimiento", "Salud", "Deudas","Otros"]

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Gastos Personales")
        self.resize(800, 500)
        db_manager.create_tables()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Top: usuarios
        h_usr = QtWidgets.QHBoxLayout()
        self.cmb_usuarios = QtWidgets.QComboBox()
        self.btn_refresh = QtWidgets.QPushButton("Refrescar")
        self.btn_nuevo = QtWidgets.QPushButton("Crear usuario")
        h_usr.addWidget(QtWidgets.QLabel("Usuario:"))
        h_usr.addWidget(self.cmb_usuarios)
        h_usr.addWidget(self.btn_refresh)
        h_usr.addWidget(self.btn_nuevo)
        layout.addLayout(h_usr)

        # Middle: acciones
        h_actions = QtWidgets.QHBoxLayout()
        self.btn_add_fijo = QtWidgets.QPushButton("Agregar gasto fijo")
        self.btn_add_variable = QtWidgets.QPushButton("Agregar gasto variable")
        self.btn_ver_gastos = QtWidgets.QPushButton("Listar gastos")
        h_actions.addWidget(self.btn_add_fijo)
        h_actions.addWidget(self.btn_add_variable)
        h_actions.addWidget(self.btn_ver_gastos)
        layout.addLayout(h_actions)

        # Extra widgets: ahorro spin y progress bar (añade más widgets distintos)
        h_extra = QtWidgets.QHBoxLayout()
        h_extra.addWidget(QtWidgets.QLabel("Ahorro %:"))
        self.spin_ahorro = QtWidgets.QSpinBox()
        self.spin_ahorro.setRange(0, 100)
        h_extra.addWidget(self.spin_ahorro)
        self.btn_update_ahorro = QtWidgets.QPushButton("Actualizar ahorro")
        h_extra.addWidget(self.btn_update_ahorro)
        h_extra.addStretch()
        self.progress_usage = QtWidgets.QProgressBar()
        self.progress_usage.setRange(0, 100)
        self.progress_usage.setFormat("%p% uso del ingreso")
        self.progress_usage.setValue(0)
        h_extra.addWidget(self.progress_usage)
        layout.addLayout(h_extra)

        # Reporte
        self.txt_reporte = QtWidgets.QTextEdit()
        self.txt_reporte.setReadOnly(True)
        layout.addWidget(self.txt_reporte)

        # Conexiones
        self.btn_refresh.clicked.connect(self.refresh_users)
        self.btn_nuevo.clicked.connect(self.create_user)
        self.cmb_usuarios.currentIndexChanged.connect(self.on_user_changed)
        self.btn_add_fijo.clicked.connect(lambda: self.show_add_gasto_dialog(tipo="fijo"))
        self.btn_add_variable.clicked.connect(lambda: self.show_add_gasto_dialog(tipo="variable"))
        self.btn_ver_gastos.clicked.connect(self.show_gastos_dialog)
        self.btn_update_ahorro.clicked.connect(self.update_ahorro)

        self.refresh_users()

    def refresh_users(self):
        self.cmb_usuarios.blockSignals(True)
        self.cmb_usuarios.clear()
        rows = db_manager.get_all_usuarios()
        for r in rows:
            uid, nombre, ingreso, ahorro = r
            self.cmb_usuarios.addItem(f"{nombre} (Ingreso: {ingreso})", uid)
        self.cmb_usuarios.blockSignals(False)
        if self.cmb_usuarios.count() > 0:
            self.cmb_usuarios.setCurrentIndex(0)
            self.on_user_changed(0)
        else:
            self.txt_reporte.setPlainText("No hay usuarios. Crea uno.")
            self.spin_ahorro.setValue(0)
            self.progress_usage.setValue(0)

    def current_usuario(self) -> Usuario | None:
        idx = self.cmb_usuarios.currentIndex()
        if idx < 0:
            return None
        uid = self.cmb_usuarios.itemData(idx)
        return Usuario.from_db(int(uid))

    def create_user(self):
        nombre, ok = QtWidgets.QInputDialog.getText(self, "Crear usuario", "Nombre:")
        if not ok or not nombre.strip():
            return
        ingreso, ok = QtWidgets.QInputDialog.getDouble(self, "Crear usuario", "Ingreso mensual:", decimals=2, min=0.0)
        if not ok:
            return
        ahorro, ok = QtWidgets.QInputDialog.getDouble(self, "Crear usuario", "Porcentaje de ahorro (ej. 10):", decimals=2, min=0.0)
        if not ok:
            return
        # insertar y refrescar
        db_manager.insert_usuario(nombre.strip(), float(ingreso), float(ahorro))
        self.refresh_users()

    def on_user_changed(self, index):
        u = self.current_usuario()
        if not u:
            self.txt_reporte.setPlainText("No hay usuario seleccionado.")
            return
        # actualizar spin con el porcentaje actual
        try:
            self.spin_ahorro.blockSignals(True)
            self.spin_ahorro.setValue(int(u.ahorro_porcentaje))
        finally:
            self.spin_ahorro.blockSignals(False)
        self.update_report(u)

    def update_ahorro(self):
        u = self.current_usuario()
        if not u:
            QtWidgets.QMessageBox.warning(self, "Atención", "Selecciona un usuario primero.")
            return
        nuevo_pct = self.spin_ahorro.value()
        db_manager.update_usuario(u.id, u.nombre, u.ingreso, float(nuevo_pct))
        # recargar y refrescar
        self.refresh_users()

    def update_report(self, u: Usuario):
        texto = []
        texto.append(f"Usuario: {u.nombre} (id={u.id})")
        texto.append(f"Ingreso: {u.ingreso:.2f}")
        texto.append(f"Ahorro ({u.ahorro_porcentaje}%): {u.calcular_ahorro():.2f}")
        texto.append(f"Gastos fijos totales: {u.gastos_fijos_totales():.2f}")
        texto.append(f"Gastos variables totales: {u.gastos_variables_totales():.2f}")
        texto.append(f"Presupuesto disponible (ingreso - ahorro - gastos fijos - gastos variables): {u.presupuesto_disponible():.2f}")

        # estado y advertencia si compromiso supera ingreso
        compromiso = u.compromiso_total()
        texto.append(f"Total comprometido (ahorro + gastos): {compromiso:.2f}")
        if u.ingreso > 0:
            pct = int(min(100, (compromiso / u.ingreso) * 100))
        else:
            pct = 0
        self.progress_usage.setValue(pct)

        if compromiso > u.ingreso:
            # Advertencia visible + cuadro
            texto.append("ADVERTENCIA: Compras + ahorro exceden el ingreso. Revisa gastos o porcentaje de ahorro.")
            QtWidgets.QMessageBox.warning(self, "Advertencia", "El total comprometido (ahorro + gastos) supera el ingreso. Ajusta gastos o ahorro.")
        self.txt_reporte.setPlainText("\n".join(texto))

    def show_add_gasto_dialog(self, tipo: str):
        u = self.current_usuario()
        if not u:
            QtWidgets.QMessageBox.warning(self, "Atención", "Selecciona un usuario primero.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Agregar gasto fijo" if tipo == "fijo" else "Agregar gasto variable")
        form = QtWidgets.QFormLayout(dlg)

        cmb_cat = QtWidgets.QComboBox()
        cmb_cat.addItems(CATEGORIES)
        form.addRow("Categoría:", cmb_cat)

        spin_monto = QtWidgets.QDoubleSpinBox()
        spin_monto.setDecimals(2)
        spin_monto.setRange(0.0, 1_000_000.0)
        form.addRow("Monto:", spin_monto)

        date_edit = None
        if tipo == "variable":
            date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            form.addRow("Fecha:", date_edit)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        form.addRow(btns)

        def on_accept():
            categoria = cmb_cat.currentText()
            monto = float(spin_monto.value())
            fecha = None
            if tipo == "variable":
                fecha = date_edit.date().toString("yyyy-MM-dd")
            if monto <= 0:
                QtWidgets.QMessageBox.information(dlg, "Monto inválido", "Ingresa un monto mayor a 0.")
                return
            if tipo == "fijo":
                u.agregar_gasto_fijo(categoria, monto)
            else:
                u.agregar_gasto_variable(categoria, monto, fecha)
            dlg.accept()

        btns.accepted.connect(on_accept)
        btns.rejected.connect(dlg.reject)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            u = Usuario.from_db(u.id)
            self.update_report(u)

    def show_gastos_dialog(self):
        u = self.current_usuario()
        if not u:
            QtWidgets.QMessageBox.warning(self, "Atención", "Selecciona un usuario primero.")
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"Gastos de {u.nombre}")
        dlg.resize(700, 450)
        v = QtWidgets.QVBoxLayout(dlg)

        tabs = QtWidgets.QTabWidget()
        v.addWidget(tabs)

        # Gastos fijos
        tbl_f = QtWidgets.QTableWidget()
        gf = u.listar_gastos_fijos()
        tbl_f.setColumnCount(3)
        tbl_f.setHorizontalHeaderLabels(["id", "categoría", "monto"])
        tbl_f.setRowCount(len(gf))
        for i, g in enumerate(gf):
            tbl_f.setItem(i, 0, QtWidgets.QTableWidgetItem(str(g.id)))
            tbl_f.setItem(i, 1, QtWidgets.QTableWidgetItem(g.categoria))
            tbl_f.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{g.monto:.2f}"))
        tbl_f.resizeColumnsToContents()
        tabs.addTab(tbl_f, "Gastos fijos")

        # botones para gastos fijos
        h_f = QtWidgets.QHBoxLayout()
        btn_edit_f = QtWidgets.QPushButton("Editar seleccionado (fijo)")
        btn_del_f = QtWidgets.QPushButton("Eliminar seleccionado (fijo)")
        h_f.addWidget(btn_edit_f)
        h_f.addWidget(btn_del_f)
        v.addLayout(h_f)

        # Gastos variables
        tbl_v = QtWidgets.QTableWidget()
        gv = u.listar_gastos_variables()
        tbl_v.setColumnCount(4)
        tbl_v.setHorizontalHeaderLabels(["id", "categoría", "monto", "fecha"])
        tbl_v.setRowCount(len(gv))
        for i, g in enumerate(gv):
            tbl_v.setItem(i, 0, QtWidgets.QTableWidgetItem(str(g.id)))
            tbl_v.setItem(i, 1, QtWidgets.QTableWidgetItem(g.categoria))
            tbl_v.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{g.monto:.2f}"))
            tbl_v.setItem(i, 3, QtWidgets.QTableWidgetItem(g.fecha))
        tbl_v.resizeColumnsToContents()
        tabs.addTab(tbl_v, "Gastos variables")

        # botones para gastos variables
        h_v = QtWidgets.QHBoxLayout()
        btn_edit_v = QtWidgets.QPushButton("Editar seleccionado (variable)")
        btn_del_v = QtWidgets.QPushButton("Eliminar seleccionado (variable)")
        h_v.addWidget(btn_edit_v)
        h_v.addWidget(btn_del_v)
        v.addLayout(h_v)

        btn_close = QtWidgets.QPushButton("Cerrar")
        btn_close.clicked.connect(dlg.accept)
        v.addWidget(btn_close)

        # -- funciones de edición/eliminación --
        def get_selected_id(table: QtWidgets.QTableWidget):
            sel = table.currentRow()
            if sel < 0:
                return None
            item = table.item(sel, 0)
            if not item:
                return None
            try:
                return int(item.text())
            except Exception:
                return None

        def refresh_tables():
            # recarga datos desde BD y actualiza tablas y reporte
            new_u = Usuario.from_db(u.id)
            # recargar fijos
            rows_f = new_u.listar_gastos_fijos()
            tbl_f.setRowCount(len(rows_f))
            for i, g in enumerate(rows_f):
                tbl_f.setItem(i, 0, QtWidgets.QTableWidgetItem(str(g.id)))
                tbl_f.setItem(i, 1, QtWidgets.QTableWidgetItem(g.categoria))
                tbl_f.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{g.monto:.2f}"))
            tbl_f.resizeColumnsToContents()
            # recargar variables
            rows_v = new_u.listar_gastos_variables()
            tbl_v.setRowCount(len(rows_v))
            for i, g in enumerate(rows_v):
                tbl_v.setItem(i, 0, QtWidgets.QTableWidgetItem(str(g.id)))
                tbl_v.setItem(i, 1, QtWidgets.QTableWidgetItem(g.categoria))
                tbl_v.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{g.monto:.2f}"))
                tbl_v.setItem(i, 3, QtWidgets.QTableWidgetItem(g.fecha))
            tbl_v.resizeColumnsToContents()
            # actualizar reporte principal
            self.update_report(new_u)

        def edit_fixed():
            gid = get_selected_id(tbl_f)
            if gid is None:
                QtWidgets.QMessageBox.information(dlg, "Selecciona", "Selecciona una fila de gasto fijo.")
                return
            # obtener fila actual del gasto
            rows = db_manager.get_gastos_fijos(u.id)
            row = next((r for r in rows if r[0] == gid), None)
            if not row:
                QtWidgets.QMessageBox.information(dlg, "No encontrado", "Gasto no encontrado.")
                return
            _, usuario_id, categoria, monto = row
            # diálogo editar (prefill)
            dlg2 = QtWidgets.QDialog(self)
            dlg2.setWindowTitle("Editar gasto fijo")
            form = QtWidgets.QFormLayout(dlg2)
            cmb = QtWidgets.QComboBox()
            cmb.addItems(CATEGORIES)
            if categoria in CATEGORIES:
                cmb.setCurrentIndex(CATEGORIES.index(categoria))
            form.addRow("Categoría:", cmb)
            spin = QtWidgets.QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setRange(0.0, 1_000_000.0)
            spin.setValue(float(monto))
            form.addRow("Monto:", spin)
            btns2 = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            form.addRow(btns2)

            def on_ok2():
                new_cat = cmb.currentText()
                new_monto = float(spin.value())
                if new_monto <= 0:
                    QtWidgets.QMessageBox.information(dlg2, "Monto inválido", "Ingresa un monto mayor a 0.")
                    return
                db_manager.update_gasto_fijo(gid, new_cat, new_monto)
                dlg2.accept()

            btns2.accepted.connect(on_ok2)
            btns2.rejected.connect(dlg2.reject)
            if dlg2.exec_() == QtWidgets.QDialog.Accepted:
                refresh_tables()

        def delete_fixed():
            gid = get_selected_id(tbl_f)
            if gid is None:
                QtWidgets.QMessageBox.information(dlg, "Selecciona", "Selecciona una fila de gasto fijo.")
                return
            if QtWidgets.QMessageBox.question(dlg, "Confirmar", "Eliminar gasto fijo seleccionado?") != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            db_manager.delete_gasto_fijo(gid)
            refresh_tables()

        def edit_variable():
            gid = get_selected_id(tbl_v)
            if gid is None:
                QtWidgets.QMessageBox.information(dlg, "Selecciona", "Selecciona una fila de gasto variable.")
                return
            rows = db_manager.get_gastos_variables(u.id)
            row = next((r for r in rows if r[0] == gid), None)
            if not row:
                QtWidgets.QMessageBox.information(dlg, "No encontrado", "Gasto no encontrado.")
                return
            _, usuario_id, categoria, monto, fecha = row
            dlg2 = QtWidgets.QDialog(self)
            dlg2.setWindowTitle("Editar gasto variable")
            form = QtWidgets.QFormLayout(dlg2)
            cmb = QtWidgets.QComboBox()
            cmb.addItems(CATEGORIES)
            if categoria in CATEGORIES:
                cmb.setCurrentIndex(CATEGORIES.index(categoria))
            form.addRow("Categoría:", cmb)
            spin = QtWidgets.QDoubleSpinBox()
            spin.setDecimals(2)
            spin.setRange(0.0, 1_000_000.0)
            spin.setValue(float(monto))
            form.addRow("Monto:", spin)
            date_edit = QtWidgets.QDateEdit()
            try:
                date_edit.setDate(QtCore.QDate.fromString(fecha, "yyyy-MM-dd"))
            except Exception:
                date_edit.setDate(QtCore.QDate.currentDate())
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            form.addRow("Fecha:", date_edit)
            btns2 = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            form.addRow(btns2)

            def on_ok3():
                new_cat = cmb.currentText()
                new_monto = float(spin.value())
                new_fecha = date_edit.date().toString("yyyy-MM-dd")
                if new_monto <= 0:
                    QtWidgets.QMessageBox.information(dlg2, "Monto inválido", "Ingresa un monto mayor a 0.")
                    return
                db_manager.update_gasto_variable(gid, new_cat, new_monto, new_fecha)
                dlg2.accept()

            btns2.accepted.connect(on_ok3)
            btns2.rejected.connect(dlg2.reject)
            if dlg2.exec_() == QtWidgets.QDialog.Accepted:
                refresh_tables()

        def delete_variable():
            gid = get_selected_id(tbl_v)
            if gid is None:
                QtWidgets.QMessageBox.information(dlg, "Selecciona", "Selecciona una fila de gasto variable.")
                return
            if QtWidgets.QMessageBox.question(dlg, "Confirmar", "Eliminar gasto variable seleccionado?") != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            db_manager.delete_gasto_variable(gid)
            refresh_tables()

        # conectar botones
        btn_edit_f.clicked.connect(edit_fixed)
        btn_del_f.clicked.connect(delete_fixed)
        btn_edit_v.clicked.connect(edit_variable)
        btn_del_v.clicked.connect(delete_variable)

        dlg.exec_()

def main():
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()