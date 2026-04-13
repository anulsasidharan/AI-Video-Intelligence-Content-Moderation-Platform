export function Footer() {
  return (
    <footer className="border-t border-border bg-background px-6 py-3">
      <p className="text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} VidShield AI. All rights reserved.
      </p>
    </footer>
  );
}
