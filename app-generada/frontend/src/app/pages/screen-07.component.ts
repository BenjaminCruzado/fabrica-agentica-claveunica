import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-07', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-07.component.html'})
export class Screen07Component {
  api = inject(PortalApiService);
  screen = {"actions":["Verificar correo","Actualizar telefono"],"fields":["Correo","Telefono","Canal preferente"],"moduleName":"Perfil ciudadano","records":[["Correo","benjamin@example.local","verificado"],["Telefono","+56 9 0000 0000","pendiente"]],"route":"/perfil/contact","summary":"Datos de contacto: implementa campos Correo, Telefono, Canal preferente y acciones Verificar correo, Actualizar telefono.","title":"Datos de contacto"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
