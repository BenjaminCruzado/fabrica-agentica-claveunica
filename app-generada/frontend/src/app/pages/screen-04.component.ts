import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-04', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-04.component.html'})
export class Screen04Component {
  api = inject(PortalApiService);
  screen = {"actions":["Buscar","Iniciar tramite","Guardar favorito"],"fields":["Categoria","Institucion","Disponibilidad"],"moduleName":"Portal ciudadano","records":[["ClaveUnica","Registro Civil","24/7"],["Domicilio","MINSEGPRES","web"],["Certificados","Municipalidad","mixto"]],"route":"/portal/catalog","summary":"Catalogo de tramites: implementa campos Categoria, Institucion, Disponibilidad y acciones Buscar, Iniciar tramite, Guardar favorito.","title":"Catalogo de tramites"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
