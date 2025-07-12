---
title: Algorithms for Fast Polynomial Evaluation
tags: ["mathematics", "algorithms"]
libs: ["mathjax","mermaidjs"]
libs_config:
    mathjax:
        declarations:
          - name: \nl
            value: \\
          - name: \RR
            value: \mathbb{R}
          - name: \order
            value: \mathcal{O}
    mermaidjs:
        flowchart:
            padding: 0
            nodeSpacing: 25
            rankSpacing: 25
---

This post is a follow-on to my previous one on [Fast Cubic Evaluation][1]. I got
to thinking about how the algorithms discussed there could be generalized to
polynomials of arbitrary degree --- say @@p@@ of degree @@N@@. Estrin's Scheme
works out-of-the-box. Horner's Scheme and Knuth's Algorithm are unworkable in
hardware though, since na&iuml;vely translating them both gives a critical path
of length @@\order(N)@@.

The strategy I came up with was to factor the polynomial in question @@p@@ into
quadratics, writing[^1]

%% p(x) = k \cdot (x^2 + a_1 x + b_1) \cdots (x^2 + a_{N/2} x + b_{N/2}). %%

This is always possible due to the fundamental theorem of algebra and the
complex conjugate root theorem. We write @@p@@ this way because it naturally
gives a parallel algorithm for evaluating @@p(x)@@. Each factor is evaluated in
parallel, then a reduction network is used to multiply them all together.

With this Factorization-Based Algorithm, each of the @@N/2@@ terms needs two
adders, but just one multiplier since the @@x^2@@ can be computed once and
reused across all the terms. The final reduction needs @@(N/2 + 1) - 1 = N/2@@
multipliers. In total, @@N@@ adders and @@N@@ multipliers are needed. So, this
algorithm matches the hardware requirements of Horner's Scheme. However, its
critical path is much shorter. Each factor has one multiplier and two adders on
its critical path, and the final reduction has a critical path of @@\lceil
\log(N/2+1) \rceil@@[^2] multipliers. Compare these figures to Estrin's Scheme,
which has @@\lceil \log(N+1) \rceil@@ multipliers and @@\lceil \log(N+1)
\rceil@@ adders on its critical path. Ultimately, preprocessing allows this
Factorization-Based Algorithm to achieve a shorter critical path than Estrin's
Scheme while also saving area.

Claude suggested that I add worked example for this algorithm. So, consider
@@N=5@@ and

%% p(x) = x^5 + 2x^4 + 3x^3 + 4x^2 + 5x + 6. %%

The polynomial @@p@@ has roots

%%
\begin{align\*}
  r_1 &\approx -1.492 \nl
  r_2 &\approx -0.806 + 1.223i \nl
  r_3 &\approx -0.806 - 1.223i \nl
  r_4 &\approx 0.552 + 1.253i \nl
  r_5 &\approx 0.552 - 1.253i.
\end{align\*}
%%

The roots @@r_2@@ and @@r_3@@ are conjugates, as are @@r_4@@ and @@r_5@@. Those
roots have to be merged to form quadratics, while the remaining roots can be
merged. Ultimately, we write

%% p(x) = k \cdot (x + b_0) \cdot (x^2 + a_1 x + b_1) \cdot (x^2 + a_2 x + b_2), %%

where the constants are chosen such that

%%
\begin{align\*}
  k &= 1 \nl
  x + b_0 &= (x - r_1) \nl
  x^2 + a_1 x + b_1 &= (x - r_2) \cdot (x - r_3) \nl
  x^2 + a_2 x + b_2 &= (x - r_4) \cdot (x - r_5).
\end{align\*}
%%

This particular case gives

%%
\begin{align\*}
  b_0 &\approx 1.492 \nl
  a_1 &\approx 1.612 \nl
  b_1 &\approx 2.145 \nl
  a_2 &\approx 1.103 \nl
  b_2 &\approx 1.875.
\end{align\*}
%%

All of the work above only has to be done once, offline. The hardware will only
see these coefficients, at which point it can run the data-flow graph given
below.

<figure>
<pre class="mermaid">
flowchart TB
  xsqin[$$x$$]
  xsq[$$x^2$$]
  sq[$$\times$$]
  xsqin --> sq
  xsqin --> sq
  sq --> xsq

  x0[$$x$$]
  b0[$$b_0$$]
  add0[$$+$$]
  x0 --> add0
  b0 --> add0

  xsq1[$$x^2$$]
  x1[$$x$$]
  a1[$$a_1$$]
  b1[$$b_1$$]
  mult1[$$\times$$]
  add1lo[$$+$$]
  add1hi[$$+$$]
  a1 --> mult1
  x1 --> mult1
  mult1 --> add1lo
  b1 --> add1lo
  xsq1 --> add1hi
  add1lo --> add1hi

  xsq2[$$x^2$$]
  x2[$$x$$]
  a2[$$a_2$$]
  b2[$$b_2$$]
  mult2[$$\times$$]
  add2lo[$$+$$]
  add2hi[$$+$$]
  a2 --> mult2
  x2 --> mult2
  mult2 --> add2lo
  b2 --> add2lo
  xsq2 --> add2hi
  add2lo --> add2hi

  red1[$$\times$$]
  red2[$$\times$$]
  add1hi --> red1
  add2hi --> red1
  add0 --> red2
  red1 --> red2

  red2 --> Output
</pre>
<figcaption>
Data-flow graph of the Factorization-Based Algorithm on the worked example. Note
how @@x^2@@ is computed once and reused in multiple places.
</figcaption>
</figure>

That's all I have. It's not particularly original, but the idea of breaking a
polynomial into factors does give rise to a pleasingly parallel algorithm. And
note that the factoring doesn't have to continue all the way down to quadratics.
It may be profitable to stop at some higher degree, especially since more
efficient serial algorithms exist and it may not be possible to exploit such a
high degree of parallelism. As a concrete example, perhaps when evaluating a
polynomial of degree @@N=128@@, you could stop at factoring @@N=16@@ and use
Knuth's Algorithm for those eight degree sixteen terms. Knuth's Algorithm would
only require nine multipliers instead of the usual sixteen, but it is serial
which makes the critical path longer. In other words, less area can be traded
for greater latency. Also, this same idea --- of breaking polynomials down
recursively then using an efficient serial algorithm to evaluate them --- is
present in the [Rabin-Winograd Algorithm][4]

Another note: this Factorization-Based Algorithm heavily uses multipliers. They
dominate the critical path, and either way more of them are used than in Knuth's
Algorithm. This is by design. During my time on [MINOTAUR][2], I observed that
[BFloat16][3] multipliers on our technology[^3] took half the time and less area
than BFloat16 adders. Hence, this algorithm tries to keep adders off the
critical path. If the balance were to shift in favor of addition, perhaps the
na&iuml;ve scheme would work better.

Finally, Claude suggested I consider numerical stability. It is known that small
errors in roots can cascade into large errors in the final value. Considering
we're using BFloat16 with just seven mantissa bits, and I intend to store all
the coefficients with the same precision, the accuracy of the underlying model
could tank. For what it's worth, no accuracy penalty was observed on MINOTAUR
when using Horner's or Estrin's Schemes, or indeed when switching to piecewise
cubic activations. But it's still possible this aggressive factorization causes
too much error. But I haven't tested that, and frankly I don't think I will now
that I'm off MINOTAUR.


[^1]: Here, each @@a_i, b_i \in \RR@@. In general, all operations are done over
    @@\RR@@ unless explicitly stated otherwise.

[^2]: All @@\log@@s are done in base two.

[^3]: MINOTAUR was designed for TSMC16 and a 200MHz clock.


[1]: </2025/07/02/fast_cubic_evaluation.html> "Ammar Ratnani's Site: Fast Cubic Evaluation"
[2]: <https://doi.org/10.1109/VLSITechnologyandCir46783.2024.10631515> "MINOTAUR: An Edge Transformer Inference and Training Accelerator with 12 MBytes On-Chip Resistive RAM and Fine-Grained Spatiotemporal Power Gating"
[3]: <https://cloud.google.com/blog/products/ai-machine-learning/bfloat16-the-secret-to-high-performance-on-cloud-tpus> "BFloat16: The secret to high performance on Cloud TPUs"
[4]: <https://doi.org/10.1002/cpa.3160250405> "Fast evaluation of polynomials by rational preparation"
