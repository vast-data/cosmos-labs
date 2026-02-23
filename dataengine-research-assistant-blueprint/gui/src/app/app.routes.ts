import { Routes } from '@angular/router';
import { LoginComponent } from './features/auth/components/login/login.component';
import { authGuard } from './features/auth/guards/auth.guard';
import { ReportLayoutComponent } from './features/reports/components/report-layout/report-layout.component';
import { CollectionPageComponent } from './pages/collections/collection-page.component';
import { SourcesPageComponent } from './pages/sources/sources-page.component';
import { AppLayoutComponent } from './pages/layout/app-layout.component';
import { BlueprintDiagramComponent } from './pages/blueprint/blueprint-diagram.component';

export const routes: Routes = [
    { path: '', redirectTo: '/chat', pathMatch: 'full' },
    { path: 'login', component: LoginComponent },
    {
        path: '',
        component: AppLayoutComponent,
        canActivate: [authGuard],
        children: [
            {
                path: 'chat',
                children: [
                    { path: '', redirectTo: 'new', pathMatch: 'full' },
                    { path: ':chatId', component: ReportLayoutComponent },
                ],
            },
            {
                path: 'collections',
                children: [
                    { path: '', component: CollectionPageComponent },
                    { path: ':id', component: SourcesPageComponent },
                ],
            },
            {
                path: 'blueprint',
                component: BlueprintDiagramComponent,
            },
        ],
    },
];
