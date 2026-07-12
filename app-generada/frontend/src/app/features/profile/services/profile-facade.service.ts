import { Injectable } from '@angular/core';
import { FeatureApiService } from '../../../services/feature-api.service';

@Injectable({ providedIn: 'root' })
export class ProfileFacadeService {
  constructor(private api: FeatureApiService) {}
  execute(action: string, route: string) { return this.api.runFeatureAction('profile', action, route); }
}
