import {
  Component,
  OnInit,
  OnDestroy,
  Input,
  Output,
  EventEmitter,
  HostListener,
  ViewChild,
  ViewContainerRef,
  ComponentRef,
  Type,
  TemplateRef,
  EmbeddedViewRef,
  Injector,
  EnvironmentInjector,
  createComponent,
  inject
} from '@angular/core';
import { CommonModule, DOCUMENT } from '@angular/common';

import { DialogConfig, DialogRef, DialogContent } from '../../models/dialog.model';

/**
 * Component that displays a dialog window
 */
@Component({
  selector: 'app-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class DialogComponent implements OnInit, OnDestroy {
  @Input() config: DialogConfig = {};
  @Input() content: DialogContent | null = null;
  @Input() dialogRef: DialogRef | null = null;

  @ViewChild('contentContainer', { read: ViewContainerRef, static: true })
  contentContainer!: ViewContainerRef;

  @Output() backdropClick = new EventEmitter<MouseEvent>();

  private contentRef: ComponentRef<unknown> | EmbeddedViewRef<unknown> | null = null;
  private injector = inject(Injector);
  private environmentInjector = inject(EnvironmentInjector);
  private document = inject(DOCUMENT);

  ngOnInit(): void {
    this.initializeDialog();
    this.renderContent();
  }

  ngOnDestroy(): void {
    this.cleanupContent();
  }

  /**
   * Handles backdrop click events
   */
  onBackdropClick(event: MouseEvent): void {
    // Only close if clicking directly on backdrop, not on child elements
    if (event.target === event.currentTarget) {
      this.backdropClick.emit(event);
      if (!this.config.disableClose) {
        this.dialogRef?.close();
      }
    }
  }

  /**
   * Handles keyboard events
   */
  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape' && !this.config.disableClose) {
      this.dialogRef?.close();
    }
  }

  /**
   * Gets the CSS classes for the dialog panel
   */
  getPanelClasses(): string {
    const classes = ['dialog-panel'];

    if (this.config.panelClass) {
      if (Array.isArray(this.config.panelClass)) {
        classes.push(...this.config.panelClass);
      } else {
        classes.push(this.config.panelClass);
      }
    }

    return classes.join(' ');
  }

  /**
   * Gets the CSS classes for the backdrop
   */
  getBackdropClasses(): string {
    const classes = ['dialog-backdrop'];

    if (this.config.backdropClass) {
      if (Array.isArray(this.config.backdropClass)) {
        classes.push(...this.config.backdropClass);
      } else {
        classes.push(this.config.backdropClass);
      }
    }

    return classes.join(' ');
  }

  /**
   * Gets the inline styles for the dialog panel
   */
  getPanelStyles(): Record<string, string> {
    const styles: Record<string, string> = {};

    if (this.config.width) {
      styles['width'] = this.config.width;
    }

    if (this.config.height) {
      styles['height'] = this.config.height;
    }

    if (this.config.minWidth) {
      styles['minWidth'] = typeof this.config.minWidth === 'number' ? `${this.config.minWidth}px` : this.config.minWidth;
    }

    if (this.config.minHeight) {
      styles['minHeight'] = typeof this.config.minHeight === 'number' ? `${this.config.minHeight}px` : this.config.minHeight;
    }

    if (this.config.maxWidth) {
      styles['maxWidth'] = typeof this.config.maxWidth === 'number' ? `${this.config.maxWidth}px` : this.config.maxWidth;
    }

    if (this.config.maxHeight) {
      styles['maxHeight'] = typeof this.config.maxHeight === 'number' ? `${this.config.maxHeight}px` : this.config.maxHeight;
    }

    // Position styles
    if (this.config.position) {
      if (this.config.position.top) {
        styles['top'] = this.config.position.top;
      }
      if (this.config.position.bottom) {
        styles['bottom'] = this.config.position.bottom;
      }
      if (this.config.position.left) {
        styles['left'] = this.config.position.left;
      }
      if (this.config.position.right) {
        styles['right'] = this.config.position.right;
      }
    }

    return styles;
  }

  /**
   * Gets the ARIA attributes for accessibility
   */
  getAriaAttributes(): Record<string, string> {
    const attributes: Record<string, string> = {};

    attributes['role'] = this.config.role ?? 'dialog';

    if (this.config.id) {
      attributes['id'] = this.config.id;
    }

    return attributes;
  }

  private initializeDialog(): void {
    // Prevent body scroll when dialog is open
    this.document.body.style.overflow = 'hidden';

    // Set up focus trap
    this.setupFocusTrap();
  }

  private renderContent(): void {
    if (!this.content || !this.contentContainer) {
      return;
    }

    if (this.content instanceof Type) {
      // It's a component
      this.contentRef = createComponent(this.content, {
        environmentInjector: this.environmentInjector,
        elementInjector: this.injector
      });

      // Set dialog data if provided
      if (this.config.data && this.contentRef.instance) {
        // Try to inject data into component instance
        const instance = this.contentRef.instance as Record<string, unknown>;
        if ('data' in instance) {
          instance['data'] = this.config.data;
        }
      }

      // Set component instance on dialog ref
      if (this.dialogRef) {
        (this.dialogRef as any).componentInstance = this.contentRef.instance;
      }

      this.contentContainer.insert(this.contentRef.hostView);
    } else if (this.content instanceof TemplateRef) {
      // It's a template
      this.contentRef = this.contentContainer.createEmbeddedView(this.content, {
        $implicit: this.config.data,
        dialogRef: this.dialogRef
      });
    }
  }

  private cleanupContent(): void {
    // Restore body scroll
    this.document.body.style.overflow = '';

    // Destroy content
    if (this.contentRef) {
      if (this.contentRef instanceof ComponentRef) {
        this.contentRef.destroy();
      } else {
        this.contentRef.destroy();
      }
      this.contentRef = null;
    }
  }

  private setupFocusTrap(): void {
    // Basic focus trap - focus first focusable element
    setTimeout(() => {
      const focusableElements = this.getFocusableElements();
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    });
  }

  private getFocusableElements(): HTMLElement[] {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])'
    ];

    const focusableElements = this.document.querySelectorAll(focusableSelectors.join(', '));
    return Array.from(focusableElements) as HTMLElement[];
  }
}