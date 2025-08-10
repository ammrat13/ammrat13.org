# (Mostly) AI Generated Code

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def fractional_part(x):
    """Compute the fractional part {x} = x - floor(x)"""
    return x - np.floor(x)


def triangle_wave(x):
    """Compute the triangle wave T(x)"""
    frac = fractional_part(x)
    return np.where(frac <= 0.5, frac, 1 - frac)


def H1_function(x):
    """Compute H_1(x) = x + 3 * T(x)"""
    H1 = 3
    return x + H1 * triangle_wave(x)


# Create x values over the interval [-4, 4]
x = np.linspace(-4, 4, 17)
y = H1_function(x)

# Create the animation
fig_anim, ax_anim = plt.subplots()
ax_anim.plot(x, y, "k-", linewidth=2, label=r"$\mathcal{H}_1(x) = x + H_1 \cdot T(x)$")
ax_anim.set_xlabel(r"$x$", fontsize=12)
ax_anim.set_ylabel(r"$\mathcal{H}_1(x)$", fontsize=12)
ax_anim.legend(fontsize=12)
ax_anim.set_xlim(-4, 4)
ax_anim.set_ylim(-4, 6)

# Remove margins around the plot
plt.tight_layout(pad=0.0)

# Initialize the horizontal line and intersection dots
(line,) = ax_anim.plot([], [], "r--", linewidth=1)
(dots,) = ax_anim.plot([], [], "ro", markersize=8)

# Animation parameters
y_min, y_max = -2.0, 4.0
y_sweep = np.linspace(y_min, y_max, 60)


def animate(frame):
    """Animation function"""
    current_y = y_sweep[frame]

    # Update the horizontal line
    line.set_data([-4, 4], [current_y, current_y])

    # Find intersection points analytically
    intersections_x = []
    intersections_y = []

    # For H1(x) = x + 3*T(x) = y, we solve for each interval
    # T(x) = {x} when {x} <= 0.5, so x + 3*{x} = y
    # T(x) = 1 - {x} when {x} >= 0.5, so x + 3*(1 - {x}) = y

    # We need to check each integer interval [n, n+1)
    x_min, x_max = -4, 4
    for n in range(int(np.floor(x_min)), int(np.ceil(x_max))):
        # Case 1: {x} <= 0.5, so x = n + frac where frac <= 0.5
        # Equation: n + frac + 3*frac = y
        # So: 4*frac = y - n, frac = (y - n)/4
        frac1 = (current_y - n) / 4
        if 0 <= frac1 <= 0.5:
            x_sol1 = n + frac1
            if x_min <= x_sol1 <= x_max:
                intersections_x.append(x_sol1)
                intersections_y.append(current_y)

        # Case 2: {x} >= 0.5, so x = n + frac where frac >= 0.5
        # Equation: n + frac + 3*(1 - frac) = y
        # So: n + frac + 3 - 3*frac = y
        # So: n + 3 - 2*frac = y
        # So: 2*frac = n + 3 - y, frac = (n + 3 - y)/2
        frac2 = (n + 3 - current_y) / 2
        if 0.5 <= frac2 <= 1.0:
            x_sol2 = n + frac2
            if x_min <= x_sol2 <= x_max:
                intersections_x.append(x_sol2)
                intersections_y.append(current_y)

    # Update the intersection dots
    dots.set_data(intersections_x, intersections_y)

    return (line, dots)


# Create and run animation
anim = animation.FuncAnimation(
    fig_anim,
    animate,
    frames=len(y_sweep),
    interval=1000.0 / 15.0,
    blit=False,
    repeat=True,
)

# Save the animation
print("Creating animation... This may take a moment.")
anim.save("h1_plot.gif", writer="pillow", fps=15, dpi=150)
print("Animation saved as 'h1_plot.gif'")
