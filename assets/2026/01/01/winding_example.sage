import matplotlib.ticker

FNAME = "winding_example_5.png"
T_BOUND = 20
PLOT_BOUND = 7

def squish(z):
    """
    Function to squish large outputs down to a manageable range for plotting.

    Goes from ℂ → ℂ.
    """
    z_mag = abs(z)
    z_hat = z / z_mag
    return log(1 + z_mag) * z_hat

z = var('z')
t = var('t')

p = (z - 1)**5 * (z + 1)
γ = p(z = I * t)
γs = lambda s: squish(γ(t = s))

plt = parametric_plot(
    (γs(t).real(), γs(t).imag()),
    (t, -T_BOUND, T_BOUND),
    plot_points=10000,
)
plt.save(
    FNAME,
    xmin=-PLOT_BOUND,
    xmax=PLOT_BOUND,
    ymin=-PLOT_BOUND,
    ymax=PLOT_BOUND,
    dpi=1200,
    axes_labels = ['Re', 'Im'],
    fontsize=8,
    ticks = [matplotlib.ticker.NullLocator(), matplotlib.ticker.NullLocator()],
)
