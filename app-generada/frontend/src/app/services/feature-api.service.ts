import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class FeatureApiService {
  constructor(private http: HttpClient) {}

  runFeatureAction(feature: string, action: string, screenRoute: string, form: Record<string, string> = {}): Observable<any> {
    if (feature === 'procedures' && (action.includes('Iniciar') || action.includes('Continuar'))) {
      return this.http.post('/api/v1/procedures', { name: form['Nombre'] || form['Tramite'] || 'Tramite iniciado desde portal local' });
    }
    if (feature === 'procedures' && action.includes('Guardar favorito')) {
      return this.http.post('/api/v1/favorites', { source: screenRoute });
    }
    if (feature === 'notifications' && action.includes('Marcar')) {
      return this.http.post('/api/v1/notifications/read-next', { source: screenRoute });
    }
    if (feature === 'notifications' && action.includes('Guardar canal')) {
      return this.http.post('/api/v1/notifications/preferences', { channel: 'email', minPriority: 'media' });
    }
    if (feature === 'consents' && action.includes('Revocar')) {
      return this.http.post('/api/v1/consents/revoke-next', { source: screenRoute });
    }
    if (feature === 'consents' && (action.includes('Autorizar') || action.includes('Renovar'))) {
      return this.http.post('/api/v1/consent-requests', { purpose: 'Validacion ciudadana desde UI', durationDays: 30 });
    }
    if (feature === 'addresses' && (action.includes('Editar') || action.includes('Subir'))) {
      return this.http.post('/api/v1/digital-addresses', { addressLine: form['Direccion'] || 'Direccion actualizada desde portal local' });
    }
    if (feature === 'cases' && (action.includes('Adjuntar') || action.includes('Enviar comentario'))) {
      return this.http.post('/api/v1/cases/comment-next', { comment: form['Comentario'] || 'Comentario ciudadano desde portal local' });
    }
    if (feature === 'audit' && action.includes('Generar')) {
      return this.http.post('/api/v1/audit-exports', { format: 'CSV', range: '30d' });
    }
    if (feature === 'security' && action.includes('Cerrar sesion')) {
      return this.http.post('/api/v1/security/close-session', { source: screenRoute });
    }
    if (feature === 'security' && (action.includes('Ingresar') || action.includes('Recuperar') || action.includes('Registrar'))) {
      return this.http.post('/api/v1/security/login-attempt', { source: screenRoute, run: form['RUN'] || 'demo' });
    }
    if (feature === 'support' && action.includes('Crear ticket')) {
      return this.http.post('/api/v1/support-tickets', { topic: form['Asunto'] || 'Ticket generado desde portal local' });
    }
    if (feature === 'profile' && action.includes('Actualizar')) {
      return this.http.patch('/api/v1/citizens/contact', { email: 'ciudadano.actualizado@example.local' });
    }
    return this.http.post('/api/v1/workflow-events', { feature, screenRoute, action });
  }
}
