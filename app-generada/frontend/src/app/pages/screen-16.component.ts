import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-16', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-16.component.html'})
export class Screen16Component {
  api = inject(PortalApiService);
  screen = {"actions":["Guardar canal","Probar envio"],"fields":["Canal","Horario","Prioridad"],"moduleName":"Notificaciones","records":[["Email","09:00-18:00","todas"],["SMS","urgente","criticas"]],"route":"/notificaciones/notification-settings","summary":"Preferencias de aviso: implementa campos Canal, Horario, Prioridad y acciones Guardar canal, Probar envio.","title":"Preferencias de aviso"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
