---
title: Leja Points in the Knuth-Eve Algorithm
libs: ["mathjax"]
libs_config:
    mathjax:
        declarations:
          - name: \nl
            value: \\
          - name: \RR
            value: \mathbb{R}
          - name: \CC
            value: \mathbb{C}
          - name: \argmax
            value: \mathop{\mathrm{arg\,max}}
---

Recently, I've been writing a lot about the [Knuth-Eve algorithm][knutheve]. I
even wrote a Fortran implementation of it [on my GitHub][knutheve-github]. The
code there is certainly not production-ready. For starters, it panics on
failures instead of returning error codes. More importantly though, I did not
consider round-off error when writing it; the code is almost certainly not
numerically stable. That goes for both encoding and for decoding, where
low-precision formats like BF16 or even FP8 would likely be used.

Recall that the encode step of the Knuth-Eve algorithm involves repeatedly
dividing a polynomial by quadratics of the form @@(x^2 - \alpha_i)@@. We have a
set of @@\alpha_i@@ values that we need to get through, but we can freely choose
the order in which we process them. The decode step iterates through all the
@@\alpha_i@@s in the reverse order that the encode step processed them. So it
makes sense to think that we might be able to improve the numerical stability of
the decoder by judiciously sorting the @@\alpha_i@@s during the encode.

I asked Gemini about this. Specifically, I asked it about evaluating polynomials
of the form

%% p_h(x) = (((y \cdot (x - \alpha_1) + \gamma_1) \cdot (x - \alpha_2) + \gamma_2) \cdots) \cdot (x - \alpha_m) + \gamma_m. %%

[^knutheve-recovery] Gemini observed that we can distribute everything to get

%%
\begin{align\*}
    p_h(x) =\,\,&
        \gamma_m \nl
        &+ \gamma_{m-1} \cdot (x-\alpha_m) \nl
        &+ \gamma_{m-2} \cdot (x-\alpha_m)(x-\alpha_{m-1}) \nl
        &+ \cdots \nl
        &+ \gamma_1 \cdot (x-\alpha_m)(x-\alpha_{m-1})\cdots(x-\alpha_2) \nl
        &+ y \cdot (x-\alpha_m)(x-\alpha_{m-1})\cdots(x-\alpha_2)(x-\alpha_1).
\end{align\*}
%%

This looks much more complicated, and it would take many more operations to
directly evaluate. But, polynomials of this form are well-studied --- they are
in [Newton form][newton-poly]. In fact, the factorization we were using can be
seen as extension of [Horner's method][horner] to Newton polynomials.

## Newton Polynomials

The concept of Newton interpolation was new to me, so I'll spend some time on
it. It seems its main use-case is when you want to construct a polynomial
approximation for some function @@f@@ over some (for our purposes, compact) set
@@S \subset \CC@@.[^approx-ex-power][^approx-ex-matrixpoly] This approximation
is constructed incrementally. At each iteration, you pick some new point @@x_i
\in S@@ and then use it to extend the approximating polynomial @@p@@, increasing
its degree by one so that it agrees with @@f@@ at the new point @@(x_i,
y_i)@@.[^approx-idea] Normally, that step of extending @@p@@ could potentially
affect all of its terms. For example, all of the coefficients could change if
the [monomial basis][monomial-poly] is used, and the basis functions themselves
change if the [Lagrange basis][lagrange-poly] is used.

The idea behind Newton interpolation is to construct a basis where this
"invalidation" doesn't happen. Let @@n_0(x) = 1@@, @@n_1(x) = (x - x_0)@@, and
in general

%% n_d(x) = \prod_{i=0}^{d-1} (x - x_i). %%

We'll write our interpolating polynomial as a linear combination of these basis
functions; so if it has degree @@d@@, it would be

%% p_d(x) = \sum_{i=0}^d c_i \cdot n_i(x) %%

for some coefficients @@c_i@@. As a concrete example, suppose we wanted to
interpolate through the points below.

| @@i@@ | @@x_i@@ | @@y_i@@ |
|:-----:|--------:|--------:|
|   0   |    0.00 |   1.000 |
|   1   |   -1.00 |   0.500 |
|   2   |   -0.50 |   0.707 |
|   3   |   -0.25 |   0.841 |

The basis polynomials would be

%%
\begin{align\*}
n_0(x) &= 1 \nl
n_1(x) &= (x - 0.00) \nl
n_2(x) &= (x - 0.00) \cdot (x + 1.00) \nl
n_3(x) &= (x - 0.00) \cdot (x + 1.00) \cdot (x + 0.50),
\end{align\*}
%%

and the coefficients would be

%%
\begin{align\*}
c_0 &= 1.0000 \nl
c_1 &= 0.5000 \nl
c_2 &= 0.1716 \nl
c_3 &= 0.0413.
\end{align\*}
%%

As you may have noticed, unlike other polynomial interpolation schemes, the
basis polynomials used in Newton interpolation are not fixed --- they depend on
the data points. So for instance in the example above, if we sampled at @@x_2 =
-0.75@@ instead of @@-0.5@@, we would have computed

%%n_3(x) = (x - 0.00) \cdot (x + 1.00) \cdot (x + 0.75).%%

In some sense, we are tailoring the basis to our dataset. Specifically, we are
choosing the basis so that @@n_d(x_i) = 0@@ for all @@i < d@@; we're making it
so that the new basis polynomials vanish on all the datapoints we used before.
That property is what allows us to sidestep the "invalidation" I mentioned
earlier. In more detail, suppose we're on the iteration with index @@d@@ (which
is the @@(d+1)@@-th iteration) of the interpolation algorithm. We want to fit
coefficients @@c_i@@ to

%%
\begin{align\*}
p_d(x_k)
  &= \sum_{i=0}^d c_i \cdot n_i(x_k) \nl
  &= \sum_{i=0}^{d-1} c_i \cdot n_i(x_k) + c_d \cdot n_d(x_k)
\end{align\*}
%%

for @@k = 0, \cdots, d@@. But look at what happens when @@k = 0, \cdots, d-1@@.
In that case, @@n_d(x_k) = 0@@ by construction, and the equation above reduces
to

%% p_d(x_k) = \sum_{i=0}^{d-1} c_i \cdot n_i(x_k). %%

The key point is that, no matter what we pick for the last coefficient @@c_d@@,
it won't affect the value of the interpolating polynomial @@p_d@@ at the points
indexed @@k = 0, \cdots, d-1@@. In other words, we can treat fitting @@p_d@@ on
these first @@d@@ points as a subproblem. But that's exactly the problem we
solved on the previous iteration! We'll just carry the coefficients over, so
that

%% p_d(x) = p_{d-1}(x) + c_d \cdot n_d(x) %%

for all @@x@@. By construction, this interpolates the points indexed @@0,
\cdots, d-1@@. We just need make it pass through the last point @@(x_d, y_d)@@,
and that's easy enough to do by setting

%% c_d = \frac{y_d - p_{d-1}(x_d)}{n_d(x_d)}. %%

[^approx-coefcompute] The upshot is that Newton interpolation allows
incrementally computing the interpolating polynomial. Both the coefficients and
the basis functions don't change once we've computed them. I speculate this
property could be useful if we don't know beforehand how many points we'll need
to achieve some desired accuracy, or if some downstream task wants to
dynamically request greater precision when it's needed.

As a sidenote, the method I described here for computing the coefficients is not
the best one. It turns out the coefficients are [divided
differences][newton-divdiff], and the Wikipedia page for them gives an efficient
algorithm for computing them. Most importantly, it doesn't explicitly require
evaluating polynomials.

## Leja Points

As alluded to before, it appears that Newton interpolation is often used to
approximate a function @@f@@ over some set @@S \subset \CC@@. When
interpolating, we have latitude in choosing the points from @@S@@. The math will
work out no matter which points we choose, but perhaps we can improve the
numerical stability of the interpolation algorithm by choosing specific points.
[Reichel][reichel90] reviews the work done by [Leja][leja57] in this
direction[^leja-reichel], and the rest of this section essentially summarizes
what they say.

As a sidenote, it's true that their results aren't specific to Newton
interpolation; the final statement of the theorem makes no reference to Newton
polynomials. Still, they seem to consider it the "default" way of solving this
problem. Indeed, their proof involves analyzing the interpolating polynomial
when written in Newton form.

### Evaluating Numerical Stability

Let's say we fix the points @@x = \begin{pmatrix} x_0 & x_1 & \cdots &
\end{pmatrix}^\intercal@@ at which we're evaluating @@f@@ ahead of time. We'll
sample to obtain @@y = \begin{pmatrix} y_0 & y_1 & \cdots &
\end{pmatrix}^\intercal@@, and compute the interpolating polynomial @@p@@. Now
let's say we want to approximate @@f@@ at some new point, so we evaluate @@p@@
there. Unfortunately, the process of evaluating @@p@@ and even the process of
computing @@p@@ in the first place accumulate numerical errors. In reality,
we'll wind up using @@p + \delta p@@ instead. That perturbed polynomial
corresponds to some function values @@y + \delta y@@; if we had done the
interpolation (in exact arithmetic) with @@y + \delta y@@ instead of @@y@@, we
would have gotten @@p + \delta p@@ instead of @@p@@. Ultimately, we'd hope that
@@\delta y@@ isn't large compared to @@\delta p@@. If it is, that would mean
small errors when working with @@p@@ correspond to wildly different functions,
which would make it hard to accurately interpolate the function @@f@@ we
actually want.

The ideas in the last paragraph are usually expressed via the [condition
number][condnum]. It turns out that the interpolating polynomial @@p@@ is linear
in the interpolation values @@y@@, where the linear transformation is
parameterized by the interpolation points @@x@@. (That's why we chose to fix
them ahead of time.) So, we can write @@p = T_x \, y@@ then contemplate

%%
\begin{align\*}
\kappa(T_x)
  &= \max \left\[ \left( \frac{\lVert \delta y \rVert_\infty}{\lVert y \rVert_\infty} \right) \left( \frac{\lVert \delta p \rVert_{\partial S}}{\lVert p \rVert_{\partial S}} \right)^{-1} \right\] \nl
  &= \lVert T_x^{-1} \rVert \cdot \lVert T_x \rVert
\end{align\*}
%%

I decided to spend some time here reviewing the logic underlying the condition
number since I found myself getting confused with the two different norms. For
@@y@@ we're just using the [infinity norm][inftynorm], but for @@p@@ Leja uses
the maximum magnitude of the polynomial on @@\partial S@@ the boundary of the
set @@S@@ we are interpolating over. It seems like a weird choice to ignore the
interior of @@S@@ completely, until you realize that the [maximum modulus
principle][maxmod] guarantees that

%%
\lVert p \rVert_{\partial S} = \max_{x \in \partial S} |p(x)| = \max_{x \in S} |p(x)| = \lVert p \rVert_{S}
%%

(and likewise for @@\delta p@@). Regardless, a low value for @@\kappa(T_x)@@
signals numerical stability, so we seek to minimize it.

### Choosing Points for Stability

To minimize @@\kappa(T_x)@@, [Leja][leja57] proposes a "greedy" algorithm for
choosing points. Specifically, we choose the next point @@x_k@@ to maximize the
product of the distances from @@x_k@@ to all the points we chose before it:

%%
x_k = \argmax_{x \in S} \prod_{i=0}^{k-1} \left| x - x_i \right|.
%%

[^leja-pts-first] We keep choosing points until we have enough, which in our
case is when we have a polynomial of sufficiently high degree. What we get in
the end is called a sequence of Leja points on @@S@@. (It need not be unique.)

That's how they're defined, but the motivation behind Leja's algorithm is
honestly a bit of a mystery to me. Intuitively, the objective function we
maximize when choosing these points should encourage them to spread out. Indeed,
all Leja points lie on @@\partial S@@. But how is that relevant? It could be as
simple as: we're taking the norm of @@p@@ over @@\partial S@@, so that will
naturally bound @@\lVert y \rVert_\infty@@ so long as all the @@x_i@@ lie on
@@\partial S@@. I don't see how [Reichel][reichel90] would get his Formula
(2.20) otherwise.

Either way, if we choose the interpolation points @@x@@ to be Leja points, then
the condition number @@\kappa(T_x)@@ grows sub-exponentially with the degree of
the polynomial ... if the capacity of @@S@@ is one. That constraint on the
capacity is treated like a technical condition, but it's quite important for us
so we'll spend some time on it.

### The Capacity of the Underlying Set

The capacity of a compact set @@S \subset \CC@@ is defined in a bit of a
roundabout way. To compute it, you consider a particular vector field defined on
the exterior of @@S@@. It should be curl-free and divergence-free, and its flux
into @@S@@ should be @@2\pi@@. Then, we look at the potential function @@\phi@@
for this field[^leja-capacity-potential]. Far from the origin, the strength of
the vector field looks like @@|z|^{-1}@@, which means the potential function
looks like

%% \phi(x) \approx \ln \|x\| + C = \ln \frac{\|x\|}{c}, %%

for some constants @@C@@ and @@c = e^{-C}@@. By enforcing that @@\phi(x) = 0@@
on @@\partial S@@, we determine the values of the constants. The capacity of
@@S@@ is defined to be the value of @@c@@.

Intuitively, the capacity of @@S@@ seems to be a measure of its size, though
that's not immediately clear from the definition. More accurately, it seems to
be a measure of its perimeter @@\partial S@@. If @@\partial S@@ is small, the
vector field would have to become very strong to get the required flux into
@@S@@ through it. That would make climbing out of the potential to infinity more
difficult. The value of @@C@@ would increase, and @@c@@ would decrease. Vice
versa if @@\partial S@@ is large. Additionally, the capacity satisfies some
properties we'd expect from a measure of size. Scaling a set by some constant
factor scales its capacity by the same factor, for instance; so if @@S@@ has
capacity @@k@@, then @@\alpha S = \\{ \alpha x : x \in S \\}@@ has capacity
@@|\alpha| k@@.

It turns out that if @@x@@ is a sequence of Leja points on a set @@S@@ with
capacity @@c@@, then

%%
P_k := \prod_{i = 0}^{k - 1} |x_k - x_i| = \Theta(c^k),
%%

using [big-Θ notation][bigtheta].[^leja-capacity-pklim] This makes some
intuitive sense. If @@c@@ represents the size of @@S@@, then @@|x_k - x_i|@@
should scale with @@c@@. As a result, multiplying @@k@@ terms of that form
should give something that scales with @@c^k@@. Here's another way to say that.
If @@S@@ is too big, the distances between points on @@\partial S@@ will be
greater than one on average, and @@P_k@@ will explode. If @@S@@ is too small,
the distances between the points will be less than one on average, and @@P_k@@
will go to zero. For some "goldilocks" sets though, which are neither too large
nor too small, @@P_k@@ converges to some positive constant. These are precisely
the sets with capacity one.

The product @@P_k@@ shows up several times in [Reichel][reichel90]'s proof of
the statement from the last sub-section, specifically to bound @@\lVert T_x
\rVert@@. The proof assumes that @@P_k@@ neither grows nor shrinks exponentially
--- it requires @@S@@ to have capacity one. If it doesn't have unit capacity,
their workaround is to just scale it first so that it does; remember, capacity
respects scaling by a constant factor. This works, so long as the capacity of
@@S@@ is non-zero.

## Does This Apply to Us?

Now let's come back to the original question. As a reminder, we wanted to sort
the @@\alpha_i@@ in the Knuth-Eve algorithm for better numerical stability. We
related this to the problem of choosing interpolation points for polynomials in
Newton form. It would seem that sorting the @@\alpha_i@@ in Leja order would be
a good choice.

Unfortunately, [Leja][leja57]'s and [Reichel][reichel90]'s work doesn't directly
translate to our situation. We are doing Newton interpolation over the set @@S =
\\{ \alpha_1, \alpha_2, \cdots \\}@@, but (I believe) this set of isolated
points has capacity zero. There's no way to scale this set to have capacity one,
so the proof mentioned in the last section doesn't work for us. Others have
reported better numerical stability with Leja points, even outside their
original context. For instance, [Calvetti][calvetti02] considers the problem of
computing the coefficients of a polynomial in the monomial basis given its
roots, and they find sorting the roots in Leja order reduces numerical error.
But in the end, the evidence isn't particularly convincing.

I implemented Leja sorting in my implementation of the Knuth-Eve algorithm. In
the code, I incorrectly said that

{% highlight fortran %}
! NOTE: This step doesn't have a solid foundation. It seems the literature
! on this looks at the condition number when encoding, which is explicitly
! not our concern. The ordering of the roots shouldn't have an impact on the
! decoder's performance.
{% endhighlight %}

Indeed, the hope is that this could improve the decoder's numerical stability.
Unfortunately, this code isn't being used for anything, so I don't have a great
reason or a great way to benchmark it. Personally, if I were using the Knuth-Eve
algorithm for low-degree polynomials, I'd probably just try all the different
permutations of the @@\alpha_i@@, and take whatever gives the least error.

[^knutheve-recovery]: When we set @@y@@ to be what the remainder polynomial
    @@r(x)@@ evaluates to, we recover the original polynomial with @@p(x) =
    p_h(x^2)@@.

[^approx-ex-power]: For a concrete example, suppose we want to approximate
    @@f(x) = 2^x@@ over the (real) interval @@[-1, 0]@@. We might want to do
    this, say, as a subroutine of some library code that computes the function
    @@2^x@@ for arbitrary @@x \in \RR@@.

[^approx-ex-matrixpoly]: For another example, the
    [MatrixPolynomials.jl][matrixpolynomials-jl] package reduces the problem of
    approximating functions of matrices to approximating complex functions. When
    the spectrum of the input matrix is constrained, it can bound the region of
    the complex plane in which the function needs to be approximated, at which
    point it can use Newton interpolation.

[^approx-idea]: This is the same idea found in [Lagrange
    interpolation][lagrange-poly], and [polynomial
    interpolation][interpolate-poly] in general.

[^approx-coefcompute]: Note that this will never divide by zero. We defined
    @@n_d@@ in terms of its roots, and it doesn't have @@x_d@@ as a root ---
    only @@x_0, \cdots, x_{d-1}@@.

[^leja-reichel]: The main contribution of Reichel's paper seems to be proposing
    a way to use Leja's results in practice. He shows that you can get away with
    discretizing @@\partial S@@, and he proposes a way to estimate the capacity
    of @@S@@ when it is not known analytically. He also spends a lot of time on
    numerical experiments. But, Reichel's summary is still good for me, since I
    can't read French.

[^leja-pts-first]: The first point @@x_0@@ is chosen to maximize its absolute
    value @@x_0 = \argmax_{x \in S} |x|@@.

[^leja-capacity-potential]: This potential exists on the exterior of @@S@@ since
    the vector field is curl-free there. The potential will also be a harmonic
    function since the vector field is divergence-free as well.

[^leja-capacity-pklim]: More accurately, we have that @@\lim_{k \to \infty}
    P_k^{1/k} = c@@.

[knutheve]: https://en.wikipedia.org/wiki/Knuth%E2%80%93Eve_algorithm "Wikipedia: Knuth-Eve algorithm"
[knutheve-github]: https://github.com/ammrat13/knuth-eve-algorithm "GitHub: ammrat13/knuth-eve-algorithm"
[matrixpolynomials-jl]: https://www.tipota.org/MatrixPolynomials.jl/dev/ "MatrixPolynomials.jl"
[horner]: https://en.wikipedia.org/wiki/Horner%27s_method "Wikipedia: Horner's method"
[newton-poly]: https://en.wikipedia.org/wiki/Newton_polynomial "Wikipedia: Newton polynomial"
[newton-divdiff]: https://en.wikipedia.org/wiki/Divided_differences "Wikipedia: Divided differences"
[monomial-poly]: https://en.wikipedia.org/wiki/Monomial_basis "Wikipedia: Monomial basis"
[lagrange-poly]: https://en.wikipedia.org/wiki/Lagrange_polynomial "Wikipedia: Lagrange polynomial"
[interpolate-poly]: https://en.wikipedia.org/wiki/Polynomial_interpolation "Wikipedia: Polynomial interpolation"
[condnum]: https://en.wikipedia.org/wiki/Condition_number "Wikipedia: Condition number"
[inftynorm]: https://en.wikipedia.org/wiki/Uniform_norm "Wikipedia: Uniform norm"
[maxmod]: https://en.wikipedia.org/wiki/Maximum_modulus_principle "Wikipedia: Maximum modulus principle"
[bigtheta]: https://en.wikipedia.org/wiki/Big_O_notation#Hardy's_%E2%89%8D_and_Knuth's_big_%CE%98 "Wikipedia: Big O notation"
[leja57]: https://dx.doi.org/10.4064/ap-4-1-8-13 "Sur certaines suites liées aux ensembles plans et leur application à la représentation conforme"
[reichel90]: https://doi.org/10.1007/BF02017352 "Newton interpolation at Leja points"
[calvetti02]: https://doi.org/10.1023/A:1025555803588 "On the evaluation of polynomial coefficients"
