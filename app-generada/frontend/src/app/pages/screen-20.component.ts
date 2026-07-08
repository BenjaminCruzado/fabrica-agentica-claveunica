import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-20', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-20.component.html'})
export class Screen20Component {
  api = inject(PortalApiService);
  screen = {"actions":["Abrir expediente","Filtrar"],"fields":["Folio","Estado","Responsable"],"moduleName":"Expedientes","records":[["EXP-1001","en revision","Mesa ciudadana"],["EXP-1002","observado","Analista DDU"]],"route":"/expedientes/case-board","summary":"Mis expedientes: implementa campos Folio, Estado, Responsable y acciones Abrir expediente, Filtrar.","title":"Mis expedientes"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
