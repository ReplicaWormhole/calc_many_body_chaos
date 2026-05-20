import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "stanford_phi4_kernel.py"


spec = importlib.util.spec_from_file_location("stanford_phi4_kernel", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def assert_close(test_case, actual, expected, rel_tol=1e-12):
    test_case.assertTrue(
        math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=0.0),
        f"{actual!r} != {expected!r}",
    )


class StanfordPhi4KernelAcceptanceTests(unittest.TestCase):
    def test_model_driven_pipeline_returns_json_serializable_sectioned_payload(self):
        coupling = 0.36
        beta = 2.5
        mass = 0.01

        payload = module.run_stanford_phi4_pipeline(
            model=module.stanford_phi4_model(),
            coupling=coupling,
            beta=beta,
            mass=mass,
            include_numeric=False,
        )

        round_tripped = json.loads(json.dumps(payload))
        self.assertEqual(set(payload), {"model", "sk", "kernel", "leading_behavior"})
        self.assertEqual(round_tripped["model"]["name"], "Stanford matrix phi^4")
        self.assertEqual(round_tripped["model"]["interaction_power"], 4)
        self.assertEqual(
            round_tripped["model"]["lagrangian_interaction"],
            "-g^2 Tr(Phi^4)",
        )

    def test_model_driven_pipeline_derives_sk_quartic_weights_from_model(self):
        model = module.StanfordPhi4Model(
            name="custom quartic lift",
            lagrangian_interaction="-g^2 custom(Phi^4)",
            interaction_power=4,
            lift=module.BranchFieldLift(
                branch_1_r=1.0,
                branch_1_a=1.0,
                branch_2_r=1.0,
                branch_2_a=0.0,
            ),
            thermal_mass_squared_coefficient=2.0 / 3.0,
            fixed_mass_coefficient=0.025,
        )

        payload = module.run_stanford_phi4_pipeline(
            model=model,
            coupling=0.36,
            beta=2.5,
            mass=0.01,
            include_numeric=False,
        )

        self.assertEqual(
            payload["sk"]["quartic_weights_by_a_count"],
            {
                0: 0.0,
                1: 4.0,
                2: 6.0,
                3: 4.0,
                4: 1.0,
            },
        )
        self.assertEqual(
            payload["sk"]["branch_difference_coefficients"],
            {
                "r^4 a^0": 0.0,
                "r^3 a^1": 4.0,
                "r^2 a^2": 6.0,
                "r^1 a^3": 4.0,
                "r^0 a^4": 1.0,
            },
        )

    def test_model_driven_pipeline_includes_kernel_equation_metadata(self):
        payload = module.run_stanford_phi4_pipeline(
            model=module.stanford_phi4_model(),
            coupling=0.36,
            beta=2.5,
            mass=0.01,
            include_numeric=False,
        )

        kernel = payload["kernel"]
        self.assertIn("homogeneous_equation", kernel)
        self.assertIn("ingredients", kernel)
        homogeneous = kernel["homogeneous_equation"]
        self.assertIn("-i omega f(omega,p)", homogeneous["frequency_space"])
        self.assertIn("lambda_L f(P)", homogeneous["one_dimensional_form"])
        self.assertIn("P(u) = P_0 u/(1-u)", homogeneous["discretized_unit_interval_form"])
        self.assertGreaterEqual(len(kernel["ingredients"]), 4)
        ingredient_names = {ingredient["name"] for ingredient in kernel["ingredients"]}
        self.assertIn("rung-projected kernel", ingredient_names)
        self.assertIn("unit-interval symmetric form", ingredient_names)

    def test_model_driven_pipeline_reproduces_thermal_fixed_mass_and_massless_answers(self):
        coupling = 0.36
        beta = 2.5
        mass = 0.01

        payload = module.run_stanford_phi4_pipeline(
            model=module.stanford_phi4_model(),
            coupling=coupling,
            beta=beta,
            mass=mass,
            include_numeric=False,
        )

        leading = payload["leading_behavior"]
        assert_close(self, leading["thermal_mass_squared"], 2.0 * coupling / (3.0 * beta**2))
        assert_close(self, leading["thermal_mass"], math.sqrt(2.0 * coupling / (3.0 * beta**2)))
        assert_close(
            self,
            leading["fixed_mass"]["lambda_L"],
            0.025 * coupling**2 / (beta**2 * mass),
        )
        self.assertEqual(leading["fixed_mass"]["coefficient"], 0.025)
        assert_close(
            self,
            leading["massless"]["lambda_L"],
            0.031 * coupling ** 1.5 / beta,
        )
        self.assertEqual(leading["massless"]["coefficient"], 0.031)
        assert_close(
            self,
            leading["massless"]["coefficient_unrounded_from_thermal_mass"],
            0.025 / math.sqrt(2.0 / 3.0),
        )

    def test_model_driven_pipeline_can_include_small_grid_numeric_kernel_coefficient(self):
        try:
            payload = module.run_stanford_phi4_pipeline(
                model=module.stanford_phi4_model(),
                coupling=1.0,
                beta=1.0,
                mass=0.1,
                include_numeric=True,
                numeric_options={
                    "mass_beta": 0.1,
                    "grid_size": 80,
                    "y_order": 32,
                },
            )
        except RuntimeError as exc:
            self.skipTest(str(exc))

        coefficient = payload["kernel"]["numeric"]["dimensionless_coefficient"]
        self.assertGreaterEqual(coefficient, 0.020)
        self.assertLessEqual(coefficient, 0.030)

    def test_cli_pipeline_json_emits_model_driven_pipeline_payload(self):
        coupling = 0.36
        beta = 2.5
        mass = 0.01

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--coupling",
                str(coupling),
                "--beta",
                str(beta),
                "--mass",
                str(mass),
                "--pipeline-json",
                "--indent",
                "0",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(set(payload), {"model", "sk", "kernel", "leading_behavior"})
        self.assertEqual(payload["model"]["name"], "Stanford matrix phi^4")
        self.assertEqual(
            payload["sk"]["quartic_weights_by_a_count"],
            {"0": 0.0, "1": 4.0, "2": 0.0, "3": 1.0, "4": 0.0},
        )
        assert_close(self, payload["leading_behavior"]["thermal_mass_squared"], 2.0 * coupling / (3.0 * beta**2))
        assert_close(
            self,
            payload["leading_behavior"]["fixed_mass"]["lambda_L"],
            0.025 * coupling**2 / (beta**2 * mass),
        )
        assert_close(
            self,
            payload["leading_behavior"]["massless"]["lambda_L"],
            0.031 * coupling ** 1.5 / beta,
        )

    def test_thermal_mass_squared_reproduces_paper_formula(self):
        for coupling, beta in [(0.015, 1.0), (0.2, 3.0), (1.7, 0.125)]:
            with self.subTest(coupling=coupling, beta=beta):
                expected = 2.0 * coupling / (3.0 * beta**2)

                actual = module.thermal_mass_squared(coupling=coupling, beta=beta)

                assert_close(self, actual, expected)

    def test_fixed_mass_high_temperature_asymptotic_reproduces_quoted_coefficient(self):
        cases = [
            # m * beta is intentionally small in each case.
            (0.4, 0.02, 1.5),
            (1.2, 0.01, 0.75),
            (0.08, 0.04, 0.5),
        ]

        for coupling, beta, mass in cases:
            with self.subTest(coupling=coupling, beta=beta, mass=mass):
                self.assertLess(mass * beta, 0.1)
                expected = 0.025 * coupling**2 / (beta**2 * mass)

                actual = module.fixed_mass_asymptotic(
                    coupling=coupling,
                    beta=beta,
                    mass=mass,
                )

                assert_close(self, actual, expected)

    def test_massless_asymptotic_reproduces_quoted_thermal_mass_result(self):
        for coupling, beta in [(0.09, 2.0), (0.25, 0.8), (1.44, 3.5)]:
            with self.subTest(coupling=coupling, beta=beta):
                expected = 0.031 * coupling ** 1.5 / beta

                actual = module.massless_asymptotic(coupling=coupling, beta=beta)

                assert_close(self, actual, expected)

    def test_massless_coefficient_is_thermal_mass_substitution_rounded_to_paper_precision(self):
        expected_unrounded = 0.025 / math.sqrt(2.0 / 3.0)

        assert_close(
            self,
            module.MASSLESS_THERMAL_COEFFICIENT_UNROUNDED,
            expected_unrounded,
        )
        assert_close(
            self,
            module.massless_coefficient_from_thermal_mass(round_to=None),
            expected_unrounded,
        )
        self.assertEqual(module.massless_coefficient_from_thermal_mass(round_to=3), 0.031)
        self.assertEqual(module.MASSLESS_THERMAL_COEFFICIENT, 0.031)

    def test_phi4_sk_vertex_weights_are_derived_from_ra_expansion(self):
        self.assertEqual(
            module.phi4_sk_vertex_weights_by_a_count(),
            {
                0: 0.0,
                1: 4.0,
                2: 0.0,
                3: 1.0,
                4: 0.0,
            },
        )

    def test_branch_field_lift_derives_quartic_ra_polynomial(self):
        lift = module.standard_ra_branch_lift()

        coefficients = module.branch_difference_monomial_coefficients(power=4, lift=lift)

        self.assertEqual(
            coefficients,
            {
                (4, 0): 0.0,
                (3, 1): 4.0,
                (2, 2): 0.0,
                (1, 3): 1.0,
                (0, 4): 0.0,
            },
        )

    def test_stanford_model_summary_derives_sk_and_asymptotic_data(self):
        model = module.stanford_phi4_model()

        self.assertEqual(model.name, "Stanford matrix phi^4")
        self.assertEqual(model.interaction_power, 4)
        self.assertEqual(model.sk_vertex_weights_by_a_count(), module.phi4_sk_vertex_weights_by_a_count())
        self.assertEqual(model.thermal_mass_squared_coefficient, 2.0 / 3.0)
        self.assertEqual(model.fixed_mass_coefficient, 0.025)

    def test_numeric_appendix_kernel_reproduces_small_mass_coefficient(self):
        try:
            result = module.diagonalize_stanford_kernel_coefficient(
                mass_beta=0.1,
                grid_size=160,
                y_order=48,
            )
        except RuntimeError as exc:
            self.skipTest(str(exc))

        self.assertGreaterEqual(result["dimensionless_coefficient"], 0.020)
        self.assertLessEqual(result["dimensionless_coefficient"], 0.030)

    def test_numeric_kernel_uses_analytic_diagonal_limit_and_stays_symmetric(self):
        try:
            matrix = module.build_stanford_unit_interval_matrix(
                mass_beta=0.1,
                grid_size=24,
                y_order=16,
            )
        except RuntimeError as exc:
            self.skipTest(str(exc))

        self.assertTrue((matrix == matrix.T).all() or abs(matrix - matrix.T).max() < 1e-12)

    def test_numeric_kernel_default_p0_factor_is_mass_regime_aware(self):
        try:
            result = module.diagonalize_stanford_kernel_coefficient(
                mass_beta=1.0,
                grid_size=24,
                y_order=16,
            )
        except RuntimeError as exc:
            self.skipTest(str(exc))

        self.assertEqual(result["p0_factor"], 1.0)
        self.assertTrue(math.isfinite(result["dimensionless_coefficient"]))

    def test_stable_inverse_sinh_avoids_large_argument_overflow(self):
        try:
            value = module._stable_inv_sinh(1000.0)
        except RuntimeError as exc:
            self.skipTest(str(exc))

        self.assertEqual(value, 0.0)

    def test_benchmark_summary_is_json_serializable_and_contains_all_paper_answers(self):
        coupling = 0.36
        beta = 2.5
        mass = 0.01

        summary = module.benchmark_summary(coupling=coupling, beta=beta, mass=mass)

        json.dumps(summary)
        self.assertEqual(summary["inputs"], {"coupling": coupling, "beta": beta, "mass": mass})
        assert_close(self, summary["thermal_mass_squared"], 2.0 * coupling / (3.0 * beta**2))
        assert_close(self, summary["fixed_mass_asymptotic"], 0.025 * coupling**2 / (beta**2 * mass))
        assert_close(self, summary["massless_asymptotic"], 0.031 * coupling ** 1.5 / beta)
        self.assertEqual(summary["paper_coefficients"]["fixed_mass"], 0.025)
        self.assertEqual(summary["paper_coefficients"]["thermal_mass_squared"], 2.0 / 3.0)
        self.assertEqual(summary["paper_coefficients"]["massless"], 0.031)

    def test_cli_emits_benchmark_summary_as_json(self):
        coupling = 0.36
        beta = 2.5
        mass = 0.01

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--coupling",
                str(coupling),
                "--beta",
                str(beta),
                "--mass",
                str(mass),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)

        self.assertEqual(payload["inputs"], {"coupling": coupling, "beta": beta, "mass": mass})
        assert_close(self, payload["thermal_mass_squared"], 2.0 * coupling / (3.0 * beta**2))
        assert_close(self, payload["fixed_mass_asymptotic"], 0.025 * coupling**2 / (beta**2 * mass))
        assert_close(self, payload["massless_asymptotic"], 0.031 * coupling ** 1.5 / beta)

    def test_cli_can_run_numeric_kernel_acceptance_benchmark(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--coupling",
                "1.0",
                "--beta",
                "1.0",
                "--numeric-kernel",
                "--mass-beta",
                "0.1",
                "--grid-size",
                "80",
                "--y-order",
                "32",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)

        self.assertGreaterEqual(payload["dimensionless_coefficient"], 0.020)
        self.assertLessEqual(payload["dimensionless_coefficient"], 0.030)


if __name__ == "__main__":
    unittest.main()
