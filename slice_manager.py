from flask import Flask, render_template, request, redirect, url_for
import subprocess

app = Flask(__name__)

# Mapping slice IDs to slice names
slices = {
    0: "production",
    1: "management",
    2: "development"
}

slice_states = [False for _ in range(3)]

@app.route('/')
def index():
    return render_template('index.html', slice_states=slice_states)

@app.route('/activate/<int:slice_id>', methods=['POST'])
def activate_slice_route(slice_id):
    action = request.form['action']
    if action == 'activate':
        subprocess.call(f"./scripts/{slices[slice_id]}_slice.sh")
        slice_states[slice_id] = True
    else:
        subprocess.call(f'./scripts/deactivate_{slices[slice_id]}_slice.sh')
        slice_states[slice_id] = False
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
