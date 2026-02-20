# Dialog Component

This is a custom dialog component analogous to Angular Material's MatDialog.

## Features

- **Backdrop**: Clickable backdrop to close dialog
- **Keyboard Support**: Escape key closes dialog
- **Accessibility**: ARIA attributes and focus management
- **Responsive**: Adapts to mobile screens
- **Configurable**: Extensive configuration options
- **TypeScript**: Full type safety

## Usage

### Basic Usage

```typescript
import { DialogService } from '@shared';

@Component({...})
export class MyComponent {
  constructor(private dialogService: DialogService) {}

  openDialog() {
    const dialogRef = this.dialogService.open(MyDialogComponent, {
      width: '400px',
      data: { message: 'Hello World!' }
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('Dialog closed with result:', result);
    });
  }
}
```

### Dialog Component Example

```typescript
import { Component, inject } from '@angular/core';
import { DialogRef, DIALOG_DATA } from '@shared';

@Component({
  selector: 'app-my-dialog',
  standalone: true,
  template: `
    <h2>Dialog Title</h2>
    <p>{{ data.message }}</p>
    <button (click)="close()">Close</button>
  `
})
export class MyDialogComponent {
  data = inject(DIALOG_DATA);
  dialogRef = inject(DialogRef);

  close() {
    this.dialogRef.close('Dialog closed!');
  }
}
```

## Configuration Options

```typescript
interface DialogConfig {
  id?: string;
  role?: 'dialog' | 'alertdialog';
  panelClass?: string | string[];
  hasBackdrop?: boolean;
  backdropClass?: string | string[];
  disableClose?: boolean;
  width?: string;
  height?: string;
  minWidth?: string | number;
  minHeight?: string | number;
  maxWidth?: string | number;
  maxHeight?: string | number;
  position?: DialogPosition;
  data?: any;
  closeOnNavigation?: boolean;
  direction?: 'ltr' | 'rtl';
  fullscreen?: boolean;
}
```

## API

### DialogService

- `open(component, config?)`: Opens a dialog
- `closeAll()`: Closes all open dialogs
- `getDialogCount()`: Returns number of open dialogs
- `openDialogs`: Observable of open dialogs

### DialogRef

- `close(result?)`: Closes the dialog
- `afterClosed()`: Observable that emits when dialog closes
- `afterOpened()`: Observable that emits when dialog opens
- `backdropClick()`: Observable for backdrop clicks
- `keydownEvents()`: Observable for keyboard events
- `getState()`: Returns current dialog state

## Styling

The dialog uses CSS custom properties and can be customized via `panelClass` and `backdropClass` configuration options.

Default classes:
- `.dialog-backdrop`: Backdrop styling
- `.dialog-panel`: Dialog panel styling
- `.dialog-content`: Content area styling