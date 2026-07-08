import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-25', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-25.component.html'})
export class Screen25Component {
  api = inject(PortalApiService);
  screen = {"actions":["Responder","Cerrar ticket"],"fields":["Ticket","Estado","Ultima respuesta"],"moduleName":"Ayuda","records":[["TK-1001","abierto","hoy"],["TK-1002","cerrado","ayer"]],"route":"/ayuda/ticket-detail","summary":"Ticket de soporte: implementa campos Ticket, Estado, Ultima respuesta y acciones Responder, Cerrar ticket.","title":"Ticket de soporte"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
