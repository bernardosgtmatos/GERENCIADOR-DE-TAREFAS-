import flet as ft
from datetime import datetime, date, timedelta
import json
import os
from zoneinfo import ZoneInfo

class TaskApp:
    def __init__(self):
        self.tasks = []
        self.tasks_history = []
        self.data_file = "task_data.json"
        self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.tasks_history = data.get('history', [])
            except:
                self.tasks = []
                self.tasks_history = []
        else:
            self.tasks = []
            self.tasks_history = []
    
    def save_data(self):
        """Salva dados no arquivo JSON"""
        data = {
            'tasks': self.tasks,
            'history': self.tasks_history
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_task(self, task_text, has_alarm, alarm_time=None):
        """Adiciona nova tarefa"""
        task = {
            'id': len(self.tasks) + len(self.tasks_history) + 1,
            'text': task_text,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'completed': False,
            'has_alarm': has_alarm,
            'alarm_time': alarm_time,
            'date': date.today().strftime("%Y-%m-%d")
        }
        self.tasks.append(task)
        self.save_data()
        return task
    
    def complete_task(self, task_id):
        """Marca tarefa como completa"""
        for task in self.tasks:
            if task['id'] == task_id:
                task['completed'] = True
                task['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break
        self.save_data()
    
    def end_day(self):
        """Finaliza o dia e gera relatório"""
        today = date.today().strftime("%Y-%m-%d")
        completed_tasks = [t for t in self.tasks if t['completed']]
        pending_tasks = [t for t in self.tasks if not t['completed']]
        
        report = {
            'date': today,
            'total_tasks': len(self.tasks),
            'completed_tasks': len(completed_tasks),
            'pending_tasks': len(pending_tasks),
            'completed_list': completed_tasks,
            'pending_list': pending_tasks,
            'completion_rate': (len(completed_tasks) / len(self.tasks) * 100) if self.tasks else 0
        }
        
        # Move tasks para o histórico
        if self.tasks:
            self.tasks_history.append({
                'date': today,
                'tasks': self.tasks.copy(),
                'report': report
            })
            self.tasks = []
            self.save_data()
        
        return report
    
    def get_tasks_by_date(self, target_date):
        """Busca tarefas de uma data específica"""
        for history in self.tasks_history:
            if history['date'] == target_date:
                return history['tasks'], history['report']
        return [], None

def main(page: ft.Page):
    page.title = "Organizador de Tarefas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = ft.Colors.GREY_50
    
    app = TaskApp()
    
    # Estado da navegação
    current_view = "main"
    
    # Componentes da UI
    task_input = ft.TextField(
        hint_text="Digite sua tarefa aqui...",
        expand=True,
        border_radius=10,
        bgcolor=ft.Colors.WHITE,
        text_size=16,
        content_padding=15
    )
    
    alarm_switch = ft.Switch(value=False, label="Definir Alarme")
    alarm_time_picker = ft.TimePicker(
        confirm_text="Confirmar",
        cancel_text="Cancelar",
        hour_label="Hora",
        minute_label="Minuto",
    )
    alarm_time_display = ft.Text("", size=12, color=ft.Colors.GREY_600)
    
    selected_alarm_time = None
    
    def show_alarm_picker(e):
        page.overlay.append(alarm_time_picker)
        alarm_time_picker.open = True
        page.update()
    
    def on_alarm_confirmed(e):
        nonlocal selected_alarm_time
        if alarm_time_picker.value:
            selected_alarm_time = alarm_time_picker.value.strftime("%H:%M")
            alarm_time_display.value = f"⏰ Alarme definido para {selected_alarm_time}"
            alarm_time_display.update()
    
    alarm_time_picker.on_change = on_alarm_confirmed
    
    # Container de tarefas
    tasks_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    
    def refresh_tasks():
        """Atualiza a lista de tarefas"""
        tasks_container.controls.clear()
        
        if not app.tasks:
            tasks_container.controls.append(
                ft.Container(
                    content=ft.Text("📋 Nenhuma tarefa pendente", size=14, color=ft.Colors.GREY_600),
                    alignment=ft.alignment.center,
                    padding=30
                )
            )
        else:
            for task in app.tasks:
                task_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Checkbox(
                                    value=task['completed'],
                                    on_change=lambda e, t=task: toggle_task(e, t)
                                ),
                                ft.Column([
                                    ft.Text(task['text'], size=16, weight=ft.FontWeight.W500),
                                    ft.Text(f"📅 Criado: {task['created_at']}", size=11, color=ft.Colors.GREY_600),
                                    ft.Text(f"🔔 {task['alarm_time']}" if task['has_alarm'] and task.get('alarm_time') else "", size=11, color=ft.Colors.BLUE_600),
                                ], spacing=3, expand=True),
                            ], spacing=10),
                        ]),
                        padding=15,
                        border_radius=10,
                    ),
                    elevation=2,
                )
                tasks_container.controls.append(task_card)
        
        page.update()
    
    def toggle_task(e, task):
        """Alterna estado da tarefa"""
        app.complete_task(task['id'])
        refresh_tasks()
        show_snackbar(f"✅ Tarefa concluída: {task['text']}")
    
    def add_task_click(e):
        """Adiciona nova tarefa"""
        if not task_input.value or not task_input.value.strip():
            show_snackbar("⚠️ Por favor, digite uma tarefa!")
            return
        
        app.add_task(
            task_input.value.strip(),
            alarm_switch.value,
            selected_alarm_time if alarm_switch.value else None
        )
        
        task_input.value = ""
        alarm_switch.value = False
        selected_alarm_time = None
        alarm_time_display.value = ""
        refresh_tasks()
        show_snackbar("✨ Tarefa adicionada com sucesso!")
    
    def end_day_click(e):
        """Finaliza o dia e mostra relatório"""
        if not app.tasks:
            show_snackbar("📭 Não há tarefas para finalizar hoje!")
            return
        
        report = app.end_day()
        
        # Mostra relatório em diálogo
        dialog_content = ft.Column([
            ft.Text(f"📊 RELATÓRIO - {report['date']}", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"✅ Tarefas Concluídas: {report['completed_tasks']}/{report['total_tasks']}"),
            ft.Text(f"📈 Taxa de Conclusão: {report['completion_rate']:.1f}%"),
            ft.Divider(),
            ft.Text("📋 Tarefas Concluídas:", weight=ft.FontWeight.W500),
            ft.Column([ft.Text(f"• {t['text']}", size=12) for t in report['completed_list']], spacing=5),
            ft.Text("⏰ Tarefas Pendentes:", weight=ft.FontWeight.W500),
            ft.Column([ft.Text(f"• {t['text']}", size=12) for t in report['pending_list']], spacing=5),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Relatório do Dia"),
            content=ft.Container(content=dialog_content, width=400, height=400),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: close_dialog(dialog))
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()
        
        refresh_tasks()
        show_snackbar("📄 Dia finalizado! Relatório gerado.")
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    def show_history(e):
        """Mostra histórico de tarefas"""
        if not app.tasks_history:
            show_snackbar("📭 Nenhum histórico disponível ainda!")
            return
        
        history_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        for history in reversed(app.tasks_history):
            date_str = history['date']
            report = history['report']
            
            history_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"📅 {date_str}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Concluídas: {report['completed_tasks']}/{report['total_tasks']}"),
                        ft.Text(f"Taxa: {report['completion_rate']:.1f}%"),
                        ft.ElevatedButton(
                            "Ver detalhes",
                            on_click=lambda e, d=date_str: show_day_details(d),
                            style=ft.ButtonStyle(color=ft.Colors.BLUE_600)
                        )
                    ], spacing=5),
                    padding=15,
                ),
                elevation=1
            )
            history_list.controls.append(history_card)
        
        history_dialog = ft.AlertDialog(
            title=ft.Text("Histórico de Tarefas"),
            content=ft.Container(content=history_list, width=500, height=500),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: close_dialog(history_dialog))
            ],
        )
        page.dialog = history_dialog
        history_dialog.open = True
        page.update()
    
    def show_day_details(target_date):
        """Mostra detalhes de um dia específico"""
        tasks, report = app.get_tasks_by_date(target_date)
        if not tasks:
            return
        
        completed_tasks = [t for t in tasks if t['completed']]
        pending_tasks = [t for t in tasks if not t['completed']]
        
        detail_content = ft.Column([
            ft.Text(f"📅 {target_date}", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("✅ Tarefas Concluídas:", weight=ft.FontWeight.W500),
            ft.Column([ft.Text(f"• {t['text']}", size=12) for t in completed_tasks], spacing=5),
            ft.Text("⏰ Tarefas Pendentes:", weight=ft.FontWeight.W500),
            ft.Column([ft.Text(f"• {t['text']}", size=12) for t in pending_tasks], spacing=5),
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
        
        detail_dialog = ft.AlertDialog(
            title=ft.Text("Detalhes do Dia"),
            content=ft.Container(content=detail_content, width=400, height=400),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: close_dialog(detail_dialog))
            ],
        )
        page.dialog = detail_dialog
        detail_dialog.open = True
        page.update()
    
    def show_snackbar(message):
        """Mostra snackbar de notificação"""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            action="OK",
            duration=3000
        )
        page.snack_bar.open = True
        page.update()
    
    # Layout principal
    header = ft.Container(
        content=ft.Column([
            ft.Text("📝 Organizador de Tarefas", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
            ft.Text("Gerencie suas tarefas do dia de forma simples e rápida", size=14, color=ft.Colors.GREY_600),
        ]),
        margin=ft.margin.only(bottom=20)
    )
    
    input_area = ft.Container(
        content=ft.Column([
            ft.Row([task_input, ft.IconButton(ft.icons.ADD, on_click=add_task_click, icon_size=30, style=ft.ButtonStyle(color=ft.Colors.BLUE_600))]),
            ft.Row([alarm_switch, ft.IconButton(ft.icons.ACCESS_ALARM, on_click=show_alarm_picker if alarm_switch.value else None, icon_size=20)]),
            alarm_time_display
        ], spacing=10),
        bgcolor=ft.Colors.WHITE,
        padding=15,
        border_radius=15,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.GREY_300)
    )
    
    tasks_header = ft.Row([
        ft.Text("📋 Minhas Tarefas", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.IconButton(ft.icons.HISTORY, on_click=show_history, tooltip="Histórico", icon_size=24),
            ft.IconButton(ft.icons.DONE_ALL, on_click=end_day_click, tooltip="Finalizar Dia", icon_size=24, icon_color=ft.Colors.GREEN_600),
        ])
    ])
    
    main_layout = ft.Column([
        header,
        input_area,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        tasks_header,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        tasks_container,
    ], spacing=10, expand=True)
    
    # Configuração do time picker
    page.overlay.append(alarm_time_picker)
    
    # Adiciona layout à página
    page.add(main_layout)
    
    # Carrega tarefas iniciais
    refresh_tasks()
    
    # Configurações da página
    page.window_width = 450
    page.window_height = 700
    page.window_resizable = True
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
