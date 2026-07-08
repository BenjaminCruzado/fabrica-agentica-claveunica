import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-24', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-24.component.html'})
export class Screen24Component {
  api = inject(PortalApiService);
  screen = {"actions":["Abrir respuesta","Valorar"],"fields":["Pregunta","Categoria","Popularidad"],"moduleName":"Ayuda","records":[["Como cambiar domicilio","DDU","alta"],["Como revocar permiso","Datos","media"]],"route":"/ayuda/faq","summary":"Preguntas frecuentes: implementa campos Pregunta, Categoria, Popularidad y acciones Abrir respuesta, Valorar.","title":"Preguntas frecuentes"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
