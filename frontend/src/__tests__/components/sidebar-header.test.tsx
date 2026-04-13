/**
 * F-02 — Dashboard Layout: Sidebar & Header component tests
 */
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(() => ({
    user: { id: 'u1', email: 'admin@vidshield.ai', name: 'Admin User', role: 'admin' },
    isAuthenticated: true,
    isAdmin: true,
    logout: jest.fn(),
  })),
}));

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

afterEach(() => {
  jest.clearAllTimers();
  jest.clearAllMocks();
});

describe('Sidebar (F-02)', () => {
  it('renders Overview navigation link', () => {
    render(<Sidebar />);
    expect(screen.getByText('Overview')).toBeInTheDocument();
  });

  it('renders Videos navigation link', () => {
    render(<Sidebar />);
    expect(screen.getByText('Videos')).toBeInTheDocument();
  });

  it('renders Moderation Queue navigation link', () => {
    render(<Sidebar />);
    expect(screen.getByText('Moderation Queue')).toBeInTheDocument();
  });

  it('renders the VidShield brand text', () => {
    render(<Sidebar />);
    expect(screen.getByText(/vidshield/i)).toBeInTheDocument();
  });

  it('renders Live Streams link', () => {
    render(<Sidebar />);
    expect(screen.getByText('Live Streams')).toBeInTheDocument();
  });
});

describe('Header (F-02)', () => {
  it('renders a header HTML element', () => {
    const { container } = renderWithQueryClient(<Header />);
    expect(container.querySelector('header')).toBeInTheDocument();
  });

  it('renders user avatar with initials AU for "Admin User"', () => {
    renderWithQueryClient(<Header />);
    expect(screen.getByText('AU')).toBeInTheDocument();
  });

  it('renders the Notifications bell button', async () => {
    renderWithQueryClient(<Header />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Notifications/)).toBeInTheDocument();
    });
  });

  it('renders User menu button', () => {
    renderWithQueryClient(<Header />);
    expect(screen.getByLabelText('User menu')).toBeInTheDocument();
  });
});
