import { Injectable } from '@angular/core';
import { FeatureApiService } from '../../../services/feature-api.service';

@Injectable({ providedIn: 'root' })
export class SecurityFacadeService {
  constructor(private api: FeatureApiService) {}
  execute(action: string, route: string) { return this.api.runFeatureAction('security', action, route); }
}
