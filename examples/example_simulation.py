from __future__ import annotations

import prodsys


if __name__ == '__main__':

    adapter_object = prodsys.adapters.JsonProductionSystemAdapter()

    # adapter_object.read_data('examples/basic_example/example_configuration.json')
    adapter_object.read_data('examples/tutorials/control_configuration.json')
    # adapter_object.write_data("data/example_configuration.json")
    # FIXME: Limited queue sizes are not working correctly in example_configuration. Fix the issue in the error handling. 
    # FIXME: control configuration does not use R4. Fix the issue in the error handling.

    runner_object = prodsys.runner.Runner(adapter=adapter_object)
    runner_object.initialize_simulation()
    runner_object.run(20000)
    runner_object.print_results()
    # runner_object.plot_results()
    runner_object.save_results_as_csv()
    # runner_object.save_results_as_json()