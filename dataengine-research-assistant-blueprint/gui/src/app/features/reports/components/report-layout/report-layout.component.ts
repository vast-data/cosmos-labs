import { ChangeDetectionStrategy, Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterOutlet } from '@angular/router';
import {
    ResizableSplittedLayoutComponent
} from '../../../shared/components/resizable-splitted-layout/resizable-splitted-layout.component';
import {
    LeftResizableContentDirective
} from '../../../shared/components/resizable-splitted-layout/left-resizable-content.directive';
import {
    RightResizableContentDirective
} from '../../../shared/components/resizable-splitted-layout/right-resizable-content.directive';
import { ReportConversationComponent } from '../report-conversation/report-conversation.component';
import { ReportPageStoreService } from '../../services/report-page-store.service';
import { ReportViewComponent } from '../report-view/report-view.component';
import { distinctUntilChanged, map } from 'rxjs';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { GreetingMessageComponent } from '../empty-state/greeting-message.component';
import { WeatherDateComponent } from '../empty-state/weather-date.component';
import { RecentSessionsComponent } from '../empty-state/recent-sessions.component';

@Component({
  selector: 'app-report-layout',
  standalone: true,
    imports: [
        RouterOutlet,
        ResizableSplittedLayoutComponent,
        LeftResizableContentDirective,
        RightResizableContentDirective,
        ReportConversationComponent,
        ReportViewComponent,
        GreetingMessageComponent,
        WeatherDateComponent,
        RecentSessionsComponent
    ],
    providers: [ReportPageStoreService],
  templateUrl: './report-layout.component.html',
  styleUrl: './report-layout.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('fadeSlide', [
      state('void', style({
        opacity: 0,
        transform: 'translateY(-20px)'
      })),
      state('*', style({
        opacity: 1,
        transform: 'translateY(0)'
      })),
      transition(':enter', [
        animate('300ms ease-out')
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({
          opacity: 0,
          transform: 'translateY(-20px)'
        }))
      ])
    ]),
    trigger('conversationSlide', [
      state('new', style({
        flex: '0 0 auto'
      })),
      state('active', style({
        flex: '1 1 auto'
      })),
      transition('new <=> active', [
        animate('400ms ease-in-out')
      ])
    ])
  ]
})
export class ReportLayoutComponent implements OnInit {
    standaloneMode = signal(false);

    private readonly route = inject(ActivatedRoute);
    private readonly destroyRef = inject(DestroyRef);
    readonly reportsStore = inject(ReportPageStoreService);

    ngOnInit(): void {
        this.route.paramMap
            .pipe(
                map(params => params.get('chatId') ?? 'new'),
                distinctUntilChanged(),
                takeUntilDestroyed(this.destroyRef)
            )
            .subscribe(chatId => {
                this.reportsStore.loadSessionHistory(chatId);
            });
    }
}
