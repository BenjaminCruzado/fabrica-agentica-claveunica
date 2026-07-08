import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PortalApiService } from '../services/portal-api.service';

@Component({selector:'app-screen-08', standalone:true, imports:[CommonModule,FormsModule], templateUrl:'./screen-08.component.html'})
export class Screen08Component {
  api = inject(PortalApiService);
  screen = {"actions":["Guardar preferencias","Ver historial"],"fields":["Uso de datos","Canales","Retencion"],"moduleName":"Perfil ciudadano","records":[["Datos estadisticos","permitido","12 meses"],["Marketing publico","rechazado","n/a"]],"route":"/perfil/privacy","summary":"Preferencias de privacidad: implementa campos Uso de datos, Canales, Retencion y acciones Guardar preferencias, Ver historial.","title":"Preferencias de privacidad"};
  state = this.api.state;
  run(action: string) { this.api.runAction(this.screen.route, action).subscribe(); }
}
