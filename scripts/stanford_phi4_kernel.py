#!/usr/bin/env python3
"""Pure-Python Stanford matrix phi^4 ladder-kernel benchmark.

This module encodes the one-dimensional ladder-kernel benchmark summarized in
``source/weak.tex``.  The current implementation derives the SK r/a quartic
branch-difference coefficients and the thermal-mass-improved massless scaling,
while the fixed-mass numeric coefficient is the paper's reported small-mass
eigenvalue benchmark.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, Literal, Optional


THERMAL_MASS_SQUARED_COEFFICIENT = 2.0 / 3.0
FIXED_MASS_COEFFICIENT = 0.025
MASSLESS_COEFFICIENT_DECIMAL_PLACES = 3
MASSLESS_THERMAL_COEFFICIENT_UNROUNDED = FIXED_MASS_COEFFICIENT / math.sqrt(
    THERMAL_MASS_SQUARED_COEFFICIENT
)
MASSLESS_THERMAL_COEFFICIENT = round(
    MASSLESS_THERMAL_COEFFICIENT_UNROUNDED,
    MASSLESS_COEFFICIENT_DECIMAL_PLACES,
)

CaseName = Literal["fixed-mass", "massless"]


@dataclass(frozen=True)
class KernelIngredient:
    """A symbolic ingredient in the Stanford ladder-kernel construction."""

    name: str
    expression: str
    description: str
    source_label: str


@dataclass(frozen=True)
class HomogeneousEquationDescription:
    """Symbolic description of the late-time homogeneous ladder equation."""

    frequency_space: str
    time_space: str
    one_dimensional_form: str
    discretized_unit_interval_form: str
    lyapunov_definition: str
    ingredients: tuple[KernelIngredient, ...]


@dataclass(frozen=True)
class Phi4BenchmarkResult:
    """JSON-serializable result for one benchmark case."""

    case: CaseName
    lambda_coupling: float
    beta: float
    mass: Optional[float]
    effective_mass: Optional[float]
    lambda_L: float
    formula: str
    coefficient: float
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class BranchFieldLift:
    """Linear map from branch fields to the r/a basis."""

    branch_1_r: float
    branch_1_a: float
    branch_2_r: float
    branch_2_a: float


@dataclass(frozen=True)
class StanfordPhi4Model:
    """Structured data for the matrix phi^4 benchmark model."""

    name: str
    lagrangian_interaction: str
    interaction_power: int
    lift: BranchFieldLift
    thermal_mass_squared_coefficient: float
    fixed_mass_coefficient: float

    def sk_branch_coefficients_by_a_count(self) -> Dict[int, float]:
        """Return normalized SK branch-difference coefficients by a-leg count."""

        coefficients = branch_difference_monomial_coefficients(
            power=self.interaction_power,
            lift=self.lift,
        )
        return {
            a_legs: coefficients[(self.interaction_power - a_legs, a_legs)]
            for a_legs in range(self.interaction_power + 1)
        }

    def sk_vertex_weights_by_a_count(self) -> Dict[int, float]:
        """Compatibility alias for normalized branch-difference coefficients.

        These are not full Feynman vertex factors: the interaction sign,
        coupling, and real-time factor are kept outside this normalized table.
        """

        return self.sk_branch_coefficients_by_a_count()


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number")


def _clean_float(value: float) -> float:
    if abs(value) < 1e-14:
        return 0.0
    rounded = round(value)
    if math.isclose(value, rounded, rel_tol=0.0, abs_tol=1e-14):
        return float(rounded)
    return value


def standard_ra_branch_lift() -> BranchFieldLift:
    """Return phi_1 = phi_r + phi_a/2 and phi_2 = phi_r - phi_a/2."""

    return BranchFieldLift(
        branch_1_r=1.0,
        branch_1_a=0.5,
        branch_2_r=1.0,
        branch_2_a=-0.5,
    )


def branch_difference_monomial_coefficients(
    power: int,
    lift: BranchFieldLift | None = None,
) -> Dict[tuple[int, int], float]:
    """Expand phi_1^power - phi_2^power in the r/a basis.

    Keys are ``(r_power, a_power)``.  For the Stanford quartic interaction this
    gives ``4 r^3 a + r a^3``.
    """

    if power < 0:
        raise ValueError(f"power must be nonnegative, got {power}")
    if lift is None:
        lift = standard_ra_branch_lift()

    coefficients: Dict[tuple[int, int], float] = {}
    for a_power in range(power + 1):
        r_power = power - a_power
        branch_1 = (lift.branch_1_r**r_power) * (lift.branch_1_a**a_power)
        branch_2 = (lift.branch_2_r**r_power) * (lift.branch_2_a**a_power)
        coefficient = math.comb(power, a_power) * (branch_1 - branch_2)
        coefficients[(r_power, a_power)] = _clean_float(coefficient)
    return coefficients


def stanford_phi4_model() -> StanfordPhi4Model:
    """Return structured benchmark data for Stanford's matrix phi^4 model."""

    return StanfordPhi4Model(
        name="Stanford matrix phi^4",
        lagrangian_interaction="-g^2 Tr(Phi^4)",
        interaction_power=4,
        lift=standard_ra_branch_lift(),
        thermal_mass_squared_coefficient=THERMAL_MASS_SQUARED_COEFFICIENT,
        fixed_mass_coefficient=FIXED_MASS_COEFFICIENT,
    )


def model_dict(model: StanfordPhi4Model) -> Dict[str, Any]:
    """Return a JSON-ready model description."""

    return {
        "name": model.name,
        "lagrangian_interaction": model.lagrangian_interaction,
        "interaction_power": model.interaction_power,
        "branch_lift": asdict(model.lift),
        "thermal_mass_squared_coefficient": model.thermal_mass_squared_coefficient,
        "fixed_mass_coefficient": model.fixed_mass_coefficient,
    }


def derive_sk_data(model: StanfordPhi4Model) -> Dict[str, Any]:
    """Derive normalized SK r/a branch data from the model interaction."""

    coefficients = branch_difference_monomial_coefficients(
        power=model.interaction_power,
        lift=model.lift,
    )
    coefficient_map = {
        f"r^{r_power} a^{a_power}": coefficient
        for (r_power, a_power), coefficient in sorted(
            coefficients.items(),
            key=lambda item: (-item[0][0], item[0][1]),
        )
    }
    by_a_count = model.sk_branch_coefficients_by_a_count()
    return {
        "branch_lift": asdict(model.lift),
        "coefficient_normalization": (
            "coefficients of phi_1^n - phi_2^n only; multiply by the "
            "interaction sign, coupling, and real-time i factor for full vertices"
        ),
        "branch_difference_coefficients": coefficient_map,
        "branch_difference": [
            {
                "r_power": r_power,
                "a_power": a_power,
                "coefficient": coefficient,
            }
            for (r_power, a_power), coefficient in sorted(
                coefficients.items(),
                key=lambda item: (-item[0][0], item[0][1]),
            )
        ],
        "branch_coefficients_by_a_count": by_a_count,
        "quartic_weights_by_a_count": by_a_count,
        "vertex_weights_by_a_count": by_a_count,
    }


def derive_kernel_data(model: StanfordPhi4Model) -> Dict[str, Any]:
    """Return the symbolic on-shell ladder-kernel data for the benchmark model."""

    equation = homogeneous_equation_description()
    return {
        "homogeneous_equation": asdict(equation),
        "ingredients": [asdict(ingredient) for ingredient in equation.ingredients],
        "rung": {
            "wightman_lines": 2,
            "planar_one_rung_factor": 48,
            "expression": "R(k) = 48 lambda^2 int d^4p/(2 pi)^4 G_tilde(k/2+p) G_tilde(k/2-p)",
            "source": "source/weak.tex:182 and source/weak.tex:360",
        },
        "operator": {
            "type": "one-dimensional angle-averaged integral operator",
            "lyapunov_definition": equation.lyapunov_definition,
            "source": "source/weak.tex:numericsapp",
        },
        "model_interaction_power": model.interaction_power,
    }


def thermal_mass_squared(coupling: float, beta: float) -> float:
    """Return the one-loop thermal mass squared, m_th^2 = 2 lambda/(3 beta^2)."""

    _require_positive("coupling", coupling)
    _require_positive("beta", beta)
    return THERMAL_MASS_SQUARED_COEFFICIENT * coupling / (beta * beta)


def thermal_mass(coupling: float, beta: float) -> float:
    """Return m_th for the massless thermal-mass-improved benchmark."""

    return math.sqrt(thermal_mass_squared(coupling, beta))


def phi4_sk_vertex_weight(a_legs: int) -> float:
    """Return the SK r/a coefficient from (r+a/2)^4 - (r-a/2)^4."""

    if a_legs < 0 or a_legs > 4:
        raise ValueError(f"a_legs must be between 0 and 4, got {a_legs}")
    return branch_difference_monomial_coefficients(power=4)[(4 - a_legs, a_legs)]


def phi4_sk_vertex_weights_by_a_count() -> Dict[int, float]:
    """Return all quartic SK vertex weights keyed by the number of a-legs."""

    return {a_legs: phi4_sk_vertex_weight(a_legs) for a_legs in range(5)}


def fixed_mass_asymptotic(coupling: float, beta: float, mass: float) -> float:
    """Return lambda_L ~= 0.025 lambda^2/(beta^2 m) for m beta << 1."""

    _require_positive("coupling", coupling)
    _require_positive("beta", beta)
    _require_positive("mass", mass)
    return FIXED_MASS_COEFFICIENT * coupling * coupling / (beta * beta * mass)


def fixed_mass_lyapunov(coupling: float, beta: float, mass: float) -> float:
    """Backward-compatible alias for the fixed-mass Stanford asymptotic."""

    return fixed_mass_asymptotic(coupling, beta, mass)


def massless_asymptotic(coupling: float, beta: float) -> float:
    """Return lambda_L ~= 0.031 lambda^(3/2)/beta for zero bare mass.

    The coefficient is the paper-rounded value obtained by substituting
    m_th^2 = 2 lambda/(3 beta^2) into the fixed-mass result.
    """

    _require_positive("coupling", coupling)
    _require_positive("beta", beta)
    return MASSLESS_THERMAL_COEFFICIENT * math.pow(coupling, 1.5) / beta


def massless_coefficient_from_thermal_mass(round_to: int | None = MASSLESS_COEFFICIENT_DECIMAL_PLACES) -> float:
    """Derive the massless coefficient from the fixed-mass result and m_th."""

    coefficient = FIXED_MASS_COEFFICIENT / math.sqrt(THERMAL_MASS_SQUARED_COEFFICIENT)
    if round_to is None:
        return coefficient
    return round(coefficient, round_to)


def massless_thermal_mass_improved_lyapunov(coupling: float, beta: float) -> float:
    """Backward-compatible alias for the massless thermal-mass-improved result."""

    return massless_asymptotic(coupling, beta)


def _require_numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Numerical Stanford-kernel diagonalization requires numpy") from exc
    return np


def _stable_log_sinh(x: Any) -> Any:
    """Return log(sinh(x)) for positive scalar or numpy-array inputs."""

    np = _require_numpy()
    values = np.asarray(x, dtype=float)
    small = values < 20.0
    out = np.empty_like(values, dtype=float)
    out[small] = np.log(np.sinh(values[small]))
    large_values = values[~small]
    out[~small] = large_values - math.log(2.0) + np.log1p(-np.exp(-2.0 * large_values))
    if np.isscalar(x):
        return float(out)
    return out


def _stable_log_one_minus_exp_neg(x: Any) -> Any:
    """Return log(1 - exp(-x)) for positive scalar or numpy-array inputs."""

    np = _require_numpy()
    values = np.asarray(x, dtype=float)
    out = np.log(-np.expm1(-values))
    if np.isscalar(x):
        return float(out)
    return out


def _stable_inv_sinh(x: Any) -> Any:
    """Return 1/sinh(x) without overflowing at large positive x."""

    np = _require_numpy()
    values = np.asarray(x, dtype=float)
    small = values < 20.0
    out = np.empty_like(values, dtype=float)
    out[small] = 1.0 / np.sinh(values[small])
    exp_neg = np.exp(-values[~small])
    out[~small] = 2.0 * exp_neg / (1.0 - exp_neg * exp_neg)
    if np.isscalar(x):
        return float(out)
    return out


def _default_p0_factor(mass_beta: float) -> float:
    """Choose the Appendix momentum scale default by mass regime."""

    return 3.0 if mass_beta < 1.0 else 1.0


def _angle_averaged_m1(
    P: float,
    K: float,
    beta: float,
    mass: float,
    coupling: float,
    y_order: int = 64,
) -> float:
    """Evaluate the paper's angle-averaged kernel m_1(P,K)."""

    _require_positive("P", P)
    _require_positive("K", K)
    _require_positive("beta", beta)
    _require_positive("mass", mass)
    _require_positive("coupling", coupling)
    if y_order <= 0:
        raise ValueError(f"y_order must be positive, got {y_order}")

    np = _require_numpy()
    lower = abs(K - P)
    upper = K + P
    if upper <= lower:
        return 0.0

    nodes, weights = np.polynomial.legendre.leggauss(y_order)
    y = 0.5 * (upper - lower) * nodes + 0.5 * (upper + lower)
    y_weights = 0.5 * (upper - lower) * weights

    E_P = math.sqrt(P * P + mass * mass)
    E_K = math.sqrt(K * K + mass * mass)
    E_plus = E_K + E_P
    E_minus = abs(E_K - E_P)

    sqrt_plus_arg = 1.0 + 4.0 * mass * mass / (y * y - E_plus * E_plus)
    sqrt_plus = np.sqrt(np.maximum(sqrt_plus_arg, 0.0))

    x_plus_plus = 0.25 * beta * (E_plus + y * sqrt_plus)
    x_plus_minus = 0.25 * beta * (E_plus - y * sqrt_plus)

    term_plus = (
        _stable_log_sinh(x_plus_plus) - _stable_log_sinh(x_plus_minus)
    ) * _stable_inv_sinh(0.5 * beta * E_plus)
    if E_minus < 1e-12 * max(1.0, mass, P, K):
        # Limit of the second logarithmic term as E_- -> 0 at fixed y.
        term_minus = 2.0 / np.expm1(0.5 * beta * np.sqrt(y * y + 4.0 * mass * mass))
    else:
        sqrt_minus_arg = 1.0 + 4.0 * mass * mass / (y * y - E_minus * E_minus)
        sqrt_minus = np.sqrt(np.maximum(sqrt_minus_arg, 0.0))
        x_minus_plus = 0.25 * beta * (E_minus + y * sqrt_minus)
        x_minus_minus = 0.25 * beta * (E_minus - y * sqrt_minus)
        term_minus = (
            _stable_log_one_minus_exp_neg(2.0 * x_minus_plus)
            - _stable_log_one_minus_exp_neg(-2.0 * x_minus_minus)
        ) * _stable_inv_sinh(0.5 * beta * E_minus)

    integral = float(np.sum(y_weights * (term_plus + term_minus)))
    prefactor = (
        3.0
        * coupling
        * coupling
        / (((2.0 * math.pi) ** 3) * beta)
        * K
        / (P * E_P * E_K)
    )
    return prefactor * integral


def build_stanford_unit_interval_matrix(
    mass_beta: float = 0.1,
    coupling: float = 1.0,
    beta: float = 1.0,
    grid_size: int = 160,
    y_order: int = 64,
    p0_factor: Optional[float] = None,
) -> Any:
    """Build the midpoint-discretized Appendix unit-interval kernel matrix."""

    _require_positive("mass_beta", mass_beta)
    _require_positive("coupling", coupling)
    _require_positive("beta", beta)
    if p0_factor is None:
        p0_factor = _default_p0_factor(mass_beta)
    _require_positive("p0_factor", p0_factor)
    if grid_size <= 0:
        raise ValueError(f"grid_size must be positive, got {grid_size}")

    np = _require_numpy()
    mass = mass_beta / beta
    p0 = p0_factor * mass
    step = 1.0 / grid_size
    u = (np.arange(grid_size, dtype=float) + 0.5) * step
    momenta = p0 * u / (1.0 - u)
    energies = np.sqrt(momenta * momenta + mass * mass)
    D = (momenta * _stable_inv_sinh(0.5 * beta * energies)) / (1.0 - u)

    matrix = np.zeros((grid_size, grid_size), dtype=float)
    for i, P in enumerate(momenta):
        for j, K in enumerate(momenta):
            m1 = _angle_averaged_m1(P, K, beta, mass, coupling, y_order=y_order)
            m2 = p0 * P * m1 / ((1.0 - u[i]) * (1.0 - u[j]) * K)
            matrix[i, j] += step * m2
            matrix[i, i] -= step * m2 * D[j] / (3.0 * D[i])
    return matrix


def diagonalize_stanford_kernel_coefficient(
    mass_beta: float = 0.1,
    coupling: float = 1.0,
    beta: float = 1.0,
    grid_size: int = 160,
    y_order: int = 64,
    p0_factor: Optional[float] = None,
) -> Dict[str, Any]:
    """Numerically diagonalize the Appendix kernel and return the scaled coefficient."""

    np = _require_numpy()
    matrix = build_stanford_unit_interval_matrix(
        mass_beta=mass_beta,
        coupling=coupling,
        beta=beta,
        grid_size=grid_size,
        y_order=y_order,
        p0_factor=p0_factor,
    )
    if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        asymmetry = float(np.max(np.abs(matrix - matrix.T)))
        scale = float(np.max(np.abs(matrix)))
        raise RuntimeError(
            "Stanford kernel matrix is not symmetric enough for eigvalsh: "
            f"max_abs_asymmetry={asymmetry}, max_abs_entry={scale}"
        )
    eigenvalues = np.linalg.eigvalsh(matrix)
    positive = eigenvalues[eigenvalues > 0.0]
    if positive.size == 0:
        raise RuntimeError("Stanford kernel diagonalization produced no positive eigenvalues")
    lambda_L = float(positive[-1])
    mass = mass_beta / beta
    coefficient = beta * beta * mass * lambda_L / (coupling * coupling)
    return {
        "lambda_L": lambda_L,
        "dimensionless_coefficient": float(coefficient),
        "mass_beta": mass_beta,
        "grid_size": grid_size,
        "y_order": y_order,
        "p0_factor": _default_p0_factor(mass_beta) if p0_factor is None else p0_factor,
    }


def homogeneous_equation_description() -> HomogeneousEquationDescription:
    """Return symbolic descriptions of the paper's ladder-kernel equation."""

    ingredients = (
        KernelIngredient(
            name="thermal mass",
            expression="m_th^2 = 2 lambda/(3 beta^2)",
            description="One-loop mass shift used when the tree-level mass is zero.",
            source_label="source/weak.tex:oneloop",
        ),
        KernelIngredient(
            name="homogeneous ladder equation",
            expression=(
                "-i omega f(omega,p) = integral d^3k/(2 pi)^3 m(k,p) "
                "[f(omega,k) - sinh(beta E_p/2) f(omega,p)/(3 sinh(beta E_k/2))]"
            ),
            description="Late-time equation after dropping the inhomogeneous zero-rung term.",
            source_label="source/weak.tex:wholeequation",
        ),
        KernelIngredient(
            name="rung-projected kernel",
            expression="m(k,p) = [R(k_+) + R(k_-)]/(4 E_k E_p), k_+/- = (E_k +/- E_p, k-p)",
            description="On-shell kernel built from the two Wightman-rung channels.",
            source_label="source/weak.tex:232",
        ),
        KernelIngredient(
            name="rung function",
            expression="R(k) = 48 lambda^2 integral d^4p/(2 pi)^4 G_tilde(k/2+p) G_tilde(k/2-p)",
            description="Two-Wightman-line rung entering each ladder step.",
            source_label="source/weak.tex:182 and source/weak.tex:360",
        ),
        KernelIngredient(
            name="angle-averaged one-dimensional kernel",
            expression="lambda_L f(P) = integral_0^infty dK m_1(P,K) [f(K) - sinh(beta E_P/2) f(P)/(3 sinh(beta E_K/2))]",
            description="Rotationally reduced benchmark equation on the momentum half-line.",
            source_label="source/weak.tex:401 and source/weak.tex:404",
        ),
        KernelIngredient(
            name="unit-interval symmetric form",
            expression="P(u) = P_0 u/(1-u), lambda_L f_2(u) = integral_0^1 dv m_2(u,v) [f_2(v) - D(v) f_2(u)/(3 D(u))]",
            description="Uniform-discretization form used for the reported matrix benchmark.",
            source_label="source/weak.tex:414 and source/weak.tex:423",
        ),
    )
    return HomogeneousEquationDescription(
        frequency_space=(
            "-i omega f(omega,p) = integral d^3k/(2 pi)^3 m(k,p) "
            "[f(omega,k) - sinh(beta E_p/2) f(omega,p)/(3 sinh(beta E_k/2))]"
        ),
        time_space="d f / d t = M f, with M the integral operator on the right-hand side.",
        one_dimensional_form=(
            "lambda_L f(P) = integral_0^infty dK m_1(P,K) "
            "[f(K) - sinh(beta E_P/2) f(P)/(3 sinh(beta E_K/2))]"
        ),
        discretized_unit_interval_form=(
            "P(u) = P_0 u/(1-u); lambda_L f_2(u) = integral_0^1 dv m_2(u,v) "
            "[f_2(v) - D(v) f_2(u)/(3 D(u))]"
        ),
        lyapunov_definition="lambda_L is the largest positive eigenvalue of M.",
        ingredients=ingredients,
    )


def benchmark_result(
    case: CaseName,
    lambda_coupling: float,
    beta: float,
    mass: Optional[float] = None,
) -> Phi4BenchmarkResult:
    """Build a benchmark result for ``fixed-mass`` or ``massless``."""

    if case == "fixed-mass":
        if mass is None:
            raise ValueError("mass is required for the fixed-mass case")
        value = fixed_mass_asymptotic(lambda_coupling, beta, mass)
        return Phi4BenchmarkResult(
            case=case,
            lambda_coupling=lambda_coupling,
            beta=beta,
            mass=mass,
            effective_mass=mass,
            lambda_L=value,
            formula="lambda_L = 0.025 lambda^2/(beta^2 m)",
            coefficient=FIXED_MASS_COEFFICIENT,
            assumptions=("m beta << 1", "nonzero tree-level mass", "leading weak-coupling asymptotic"),
        )

    if case == "massless":
        value = massless_asymptotic(lambda_coupling, beta)
        return Phi4BenchmarkResult(
            case=case,
            lambda_coupling=lambda_coupling,
            beta=beta,
            mass=0.0,
            effective_mass=thermal_mass(lambda_coupling, beta),
            lambda_L=value,
            formula="lambda_L = 0.031 lambda^(3/2)/beta with m_th^2 = 2 lambda/(3 beta^2)",
            coefficient=MASSLESS_THERMAL_COEFFICIENT,
            assumptions=("zero bare mass", "thermal-mass improvement", "leading weak-coupling asymptotic"),
        )

    raise ValueError(f"unknown benchmark case: {case}")


def benchmark_summary(coupling: float, beta: float, mass: float) -> Dict[str, Any]:
    """Return the compact acceptance-test summary of the Stanford quoted answers."""

    return {
        "inputs": {"coupling": coupling, "beta": beta, "mass": mass},
        "thermal_mass_squared": thermal_mass_squared(coupling, beta),
        "fixed_mass_asymptotic": fixed_mass_asymptotic(coupling, beta, mass),
        "massless_asymptotic": massless_asymptotic(coupling, beta),
        "paper_coefficients": {
            "fixed_mass": FIXED_MASS_COEFFICIENT,
            "thermal_mass_squared": THERMAL_MASS_SQUARED_COEFFICIENT,
            "massless": MASSLESS_THERMAL_COEFFICIENT,
            "massless_unrounded_from_thermal_mass": MASSLESS_THERMAL_COEFFICIENT_UNROUNDED,
        },
        "sk_phi4_vertex_weights_by_a_count": phi4_sk_vertex_weights_by_a_count(),
        "formulas": {
            "thermal_mass_squared": "m_th^2 = 2 lambda/(3 beta^2)",
            "fixed_mass_asymptotic": "lambda_L = 0.025 lambda^2/(beta^2 m), m beta << 1",
            "massless_asymptotic": "lambda_L = 0.031 lambda^(3/2)/beta after thermal-mass improvement",
        },
    }


def leading_behavior_data(
    model: StanfordPhi4Model,
    coupling: float,
    beta: float,
    mass: float,
) -> Dict[str, Any]:
    """Derive the benchmark leading behaviors from model coefficients."""

    _require_positive("coupling", coupling)
    _require_positive("beta", beta)
    _require_positive("mass", mass)
    thermal_mass_sq = model.thermal_mass_squared_coefficient * coupling / (beta * beta)
    fixed_lambda_L = model.fixed_mass_coefficient * coupling * coupling / (beta * beta * mass)
    massless_unrounded_coefficient = model.fixed_mass_coefficient / math.sqrt(
        model.thermal_mass_squared_coefficient
    )
    massless_coefficient = round(
        massless_unrounded_coefficient,
        MASSLESS_COEFFICIENT_DECIMAL_PLACES,
    )
    return {
        "inputs": {"coupling": coupling, "beta": beta, "mass": mass},
        "thermal_mass_squared": thermal_mass_sq,
        "thermal_mass": math.sqrt(thermal_mass_sq),
        "fixed_mass": {
            "lambda_L": fixed_lambda_L,
            "coefficient": model.fixed_mass_coefficient,
            "formula": "lambda_L = c_fixed lambda^2/(beta^2 m)",
            "regime": "m beta << 1 with nonzero tree-level mass",
        },
        "massless": {
            "lambda_L": massless_coefficient * math.pow(coupling, 1.5) / beta,
            "coefficient": massless_coefficient,
            "coefficient_unrounded_from_thermal_mass": massless_unrounded_coefficient,
            "formula": "lambda_L = c_massless lambda^(3/2)/beta after thermal-mass improvement",
            "regime": "zero tree-level mass",
        },
    }


def run_stanford_phi4_pipeline(
    model: StanfordPhi4Model | None = None,
    coupling: float = 1.0,
    beta: float = 1.0,
    mass: float = 0.1,
    include_numeric: bool = False,
    numeric_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the model-driven Stanford phi^4 benchmark pipeline.

    The pipeline derives the normalized SK branch coefficients from ``model``,
    attaches the symbolic on-shell ladder-kernel equation, and evaluates the
    leading fixed-mass and thermal-mass-improved massless behavior.  Optional
    numerical diagonalization uses the Appendix one-dimensional kernel.
    """

    if model is None:
        model = stanford_phi4_model()
    payload = {
        "model": model_dict(model),
        "sk": derive_sk_data(model),
        "kernel": derive_kernel_data(model),
        "leading_behavior": leading_behavior_data(model, coupling, beta, mass),
    }
    if include_numeric:
        options = dict(numeric_options or {})
        options.setdefault("mass_beta", mass * beta)
        options.setdefault("coupling", coupling)
        options.setdefault("beta", beta)
        payload["kernel"]["numeric"] = diagonalize_stanford_kernel_coefficient(**options)
    return payload


def result_dict(result: Phi4BenchmarkResult, include_equation: bool = False) -> Dict[str, Any]:
    """Convert a benchmark result to a JSON-ready dictionary."""

    payload: Dict[str, Any] = asdict(result)
    if include_equation:
        payload["homogeneous_equation"] = asdict(homogeneous_equation_description())
    return payload


def results_dict(results: Iterable[Phi4BenchmarkResult], include_equation: bool = False) -> Dict[str, Any]:
    """Convert multiple benchmark results to a JSON-ready dictionary."""

    payload: Dict[str, Any] = {"results": [asdict(result) for result in results]}
    if include_equation:
        payload["homogeneous_equation"] = asdict(homogeneous_equation_description())
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print JSON for Stanford matrix phi^4 ladder-kernel asymptotic benchmarks."
    )
    parser.add_argument(
        "--case",
        choices=("fixed-mass", "massless", "both"),
        default="both",
        help="Benchmark case to print. Default: both.",
    )
    coupling_group = parser.add_mutually_exclusive_group(required=True)
    coupling_group.add_argument("--lambda", dest="lambda_coupling", type=float, help="'t Hooft coupling lambda.")
    coupling_group.add_argument("--coupling", dest="lambda_coupling", type=float, help="'t Hooft coupling lambda.")
    parser.add_argument("--beta", type=float, required=True, help="Inverse temperature beta.")
    parser.add_argument("--mass", type=float, help="Tree-level mass for --case fixed-mass or both.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the compact benchmark-summary JSON expected by the acceptance test.",
    )
    parser.add_argument(
        "--pipeline-json",
        action="store_true",
        help="Emit the model-driven SK/kernel/leading-behavior pipeline payload.",
    )
    parser.add_argument(
        "--include-equation",
        action="store_true",
        help="Include symbolic homogeneous-equation and kernel-ingredient descriptions.",
    )
    parser.add_argument(
        "--numeric-kernel",
        action="store_true",
        help="Numerically diagonalize the Appendix unit-interval kernel and print the scaled coefficient.",
    )
    parser.add_argument("--mass-beta", type=float, default=0.1, help="Dimensionless mass beta for --numeric-kernel.")
    parser.add_argument("--grid-size", type=int, default=160, help="Midpoint grid size for --numeric-kernel.")
    parser.add_argument("--y-order", type=int, default=64, help="Gauss-Legendre y quadrature order for --numeric-kernel.")
    parser.add_argument(
        "--p0-factor",
        type=float,
        default=None,
        help="P0/m value in P(u)=P0 u/(1-u); defaults to 3 for m beta < 1 and 1 otherwise.",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation. Use 0 for one-line JSON.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    indent = None if args.indent == 0 else args.indent

    if args.numeric_kernel:
        print(
            json.dumps(
                diagonalize_stanford_kernel_coefficient(
                    mass_beta=args.mass_beta,
                    coupling=args.lambda_coupling,
                    beta=args.beta,
                    grid_size=args.grid_size,
                    y_order=args.y_order,
                    p0_factor=args.p0_factor,
                ),
                indent=indent,
                sort_keys=True,
            )
        )
        return

    if args.pipeline_json:
        if args.mass is None:
            raise ValueError("--pipeline-json requires --mass")
        print(
            json.dumps(
                run_stanford_phi4_pipeline(
                    model=stanford_phi4_model(),
                    coupling=args.lambda_coupling,
                    beta=args.beta,
                    mass=args.mass,
                    include_numeric=False,
                ),
                indent=indent,
                sort_keys=True,
            )
        )
        return

    if args.json:
        if args.mass is None:
            raise ValueError("--json requires --mass so the compact summary can include both cases")
        print(
            json.dumps(
                benchmark_summary(args.lambda_coupling, args.beta, args.mass),
                indent=indent,
                sort_keys=True,
            )
        )
        return

    if args.case == "both":
        results = (
            benchmark_result("fixed-mass", args.lambda_coupling, args.beta, args.mass),
            benchmark_result("massless", args.lambda_coupling, args.beta),
        )
        print(json.dumps(results_dict(results, args.include_equation), indent=indent, sort_keys=True))
        return

    result = benchmark_result(args.case, args.lambda_coupling, args.beta, args.mass)
    print(json.dumps(result_dict(result, args.include_equation), indent=indent, sort_keys=True))


if __name__ == "__main__":
    main()
