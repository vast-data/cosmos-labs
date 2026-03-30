import { Type, TemplateRef, InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';

/**
 * Configuration options for dialog windows
 */
export interface DialogConfig<D = unknown> {
  /**
   * ID of the dialog element
   */
  id?: string;

  /**
   * The ARIA role of the dialog element
   */
  role?: 'dialog' | 'alertdialog';

  /**
   * Custom class for the overlay pane
   */
  panelClass?: string | string[];

  /**
   * Whether the dialog has a backdrop
   */
  hasBackdrop?: boolean;

  /**
   * Custom class for the backdrop
   */
  backdropClass?: string | string[];

  /**
   * Whether clicking on the backdrop should close the dialog
   */
  disableClose?: boolean;

  /**
   * Width of the dialog
   */
  width?: string;

  /**
   * Height of the dialog
   */
  height?: string;

  /**
   * Minimum width of the dialog
   */
  minWidth?: string | number;

  /**
   * Minimum height of the dialog
   */
  minHeight?: string | number;

  /**
   * Maximum width of the dialog
   */
  maxWidth?: string | number;

  /**
   * Maximum height of the dialog
   */
  maxHeight?: string | number;

  /**
   * Position strategy for the dialog
   */
  position?: DialogPosition;

  /**
   * Data to pass to the dialog component
   */
  data?: any;

  /**
   * Whether the dialog should be closable via Escape key
   */
  closeOnNavigation?: boolean;

  /**
   * Direction of the text in the dialog
   */
  direction?: 'ltr' | 'rtl';

  /**
   * Whether the dialog should be displayed in fullscreen mode
   */
  fullscreen?: boolean;

  /**
   * Animation state for the dialog
   */
  animationState?: string;
}

/**
 * Position configuration for dialog windows
 */
export interface DialogPosition {
  /**
   * Override for the dialog's top position
   */
  top?: string;

  /**
   * Override for the dialog's bottom position
   */
  bottom?: string;

  /**
   * Override for the dialog's left position
   */
  left?: string;

  /**
   * Override for the dialog's right position
   */
  right?: string;
}

/**
 * Reference to a dialog opened via the DialogService
 */
export interface DialogRef<T = any, R = any> {
  /**
   * Unique ID of the dialog
   */
  readonly id: string;

  /**
   * Instance of the component opened into the dialog
   */
  readonly componentInstance: T;

  /**
   * Observable that emits when the dialog has been closed
   */
  readonly afterClosed: Observable<R | undefined>;

  /**
   * Observable that emits when the dialog has been opened
   */
  readonly afterOpened: Observable<void>;

  /**
   * Observable that emits when the backdrop has been clicked
   */
  readonly backdropClick: Observable<MouseEvent>;

  /**
   * Observable that emits when the dialog has started closing
   */
  readonly beforeClosed: Observable<R | undefined>;

  /**
   * Observable that emits when the dialog has started opening
   */
  readonly beforeOpened: Observable<void>;

  /**
   * Observable that emits when a keydown event is targeted on the dialog
   */
  readonly keydownEvents: Observable<KeyboardEvent>;

  /**
   * Closes the dialog
   * @param result Optional result to return to the dialog opener
   */
  close(result?: R): void;

  /**
   * Gets the current state of the dialog's lifecycle
   */
  getState(): DialogState;
}

/**
 * Possible states of a dialog
 */
export type DialogState = 'opening' | 'opened' | 'closing' | 'closed';

/**
 * Type for dialog content - can be a component type or template ref
 */
export type DialogContent<T = unknown> = Type<T> | TemplateRef<T>;

/**
 * Injection token for DialogRef
 */
export const DIALOG_REF = new InjectionToken<DialogRef>('DialogRef');