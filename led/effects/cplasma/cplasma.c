#include <Python.h>
#include <math.h>
#include <stdio.h>

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
//#include <numpy/noprefix.h>
#include <numpy/arrayobject.h>
#include "noise.h"

float noise3(float x, float y, float z,
			 const int repeatx, const int repeaty, const int repeatz,
			 const int base);

inline static double make_noise(double x, double y, double z, int octaves)
// Copied out of _perlin.c of python noise module
{
	double freq = 1.0f;
	double persistence = 0.5f;
	double lacunarity = 2.0f;

	double amp = 1.0f;
	double max = 0.0f;
	double total = 0.0f;

	int repeatx = 1024;
	int repeaty = 1024;
	int repeatz = 1024;
	int base = 0;

	int i;

	for (i = 0; i < octaves; i++) {
		total += noise3(x * freq, y * freq, z * freq,
			(const int)(repeatx*freq), (const int)(repeaty*freq), (const int)(repeatz*freq), base) * amp;
		max += amp;
		freq *= lacunarity;
		amp *= persistence;
	}
	return (double) (total / max);
}

static PyObject* py_render(PyObject* self, PyObject* args)
{
	// values from python
	float zoom;
	PyObject *py_modelX, *py_modelY, *py_modelZ;
	double time_const;
	int octaves;
	double time;
	PyObject *py_frame;
	int framelen;

	// internal values
	int i;
	double z0;
	double *modelX;
	double *modelY;
	double *modelZ;
	double *scaledX;
	double *scaledY;
	double *scaledZ;
	int modelXlen;
	int modelYlen;
	int modelZlen;
	double *noise;
	double *pixels;
	double color[3] = {0, 0, 0};

    if (!PyArg_ParseTuple(args, "fOOOddiO|(ddd):render", &zoom,
			&py_modelX, &py_modelY, &py_modelZ,
			&time, &time_const, &octaves, &py_frame,
            &color[0], &color[1], &color[2]
            ))
        return NULL;

	z0 = fmod(time * time_const, 1024.0f);

    if (!PySequence_Check(py_modelX)) {
        PyErr_SetString(PyExc_TypeError, "modelX is not a sequence object");
        return NULL;
    }

    if (!PySequence_Check(py_modelY)) {
        PyErr_SetString(PyExc_TypeError, "modelY is not a sequence object");
        return NULL;
    }

    if (!PySequence_Check(py_modelZ)) {
        PyErr_SetString(PyExc_TypeError, "modelZ is not a sequence object");
        return NULL;
    }

    if (!PySequence_Check(py_frame)) {
        PyErr_SetString(PyExc_TypeError, "frame is not a sequence object");
        return NULL;
    }

    modelXlen = (int) PySequence_Length(py_modelX);
    modelYlen = (int) PySequence_Length(py_modelY);
    modelZlen = (int) PySequence_Length(py_modelZ);
	framelen = (int) PySequence_Length(py_frame);

    modelX = (double *)PyArray_DATA((PyArrayObject*)PyArray_FROM_OTF(py_modelX, NPY_DOUBLE,
			NPY_ARRAY_IN_ARRAY | NPY_ARRAY_C_CONTIGUOUS));
    modelY = (double *)PyArray_DATA((PyArrayObject*)PyArray_FROM_OTF(py_modelY, NPY_DOUBLE,
			NPY_ARRAY_IN_ARRAY | NPY_ARRAY_C_CONTIGUOUS));
    modelZ = (double *)PyArray_DATA((PyArrayObject*)PyArray_FROM_OTF(py_modelZ, NPY_DOUBLE,
			NPY_ARRAY_IN_ARRAY | NPY_ARRAY_C_CONTIGUOUS));
	pixels = (double *)PyArray_DATA((PyArrayObject*)PyArray_FROM_OTF(py_frame, NPY_DOUBLE,
		NPY_ARRAY_INOUT_ARRAY | NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_WRITEABLE |  NPY_ARRAY_UPDATEIFCOPY));

	if (modelXlen != modelYlen || modelYlen != modelZlen){
		printf("lens are %d, %d, %d\n", modelXlen, modelYlen, modelZlen);
        PyErr_SetString(PyExc_ValueError, "edgeCenters are not the same length");
        return NULL;
	}

    scaledX = PyMem_Malloc(modelXlen * sizeof(double));
	if (scaledX == NULL){  goto dealloc_scaledX; }
    scaledY = PyMem_Malloc(modelYlen * sizeof(double));
	if (scaledY == NULL){  goto dealloc_scaledY; }
    scaledZ = PyMem_Malloc(modelZlen * sizeof(double));
	if (scaledZ == NULL){  goto dealloc_scaledZ; }

    noise = PyMem_Malloc(modelXlen * sizeof(double));
	if (noise == NULL){
        PyErr_SetString(PyExc_ValueError, "failed to alloc noise");
		return PyErr_NoMemory();
	}

	for (i=0; i<modelXlen; ++i){
		scaledX[i] = modelX[i] * zoom;
		scaledY[i] = modelY[i] * zoom;
		scaledZ[i] = modelZ[i] * zoom;
	}

	Py_DECREF(modelX);
	Py_DECREF(modelY);
	Py_DECREF(modelZ);

	for(i=0; i<modelXlen; ++i) {
		noise[i] = make_noise(scaledX[i], scaledY[i], scaledZ[i]+z0, octaves);
	}

	for(i=0; i<modelXlen ; ++i) {
		noise[i] = 1.2f*noise[i] + (1.2f*0.35f);
	}
	if ( !(color[0] == 0 && color[1] == 0 && color[2] == 0) )
		for(i=0; i<framelen; ++i) {
			pixels[3*i] += noise[i] * color[0];
			pixels[3*i+1] += noise[i] * color[1];
			pixels[3*i+2] += noise[i] * color[2];
		}
	else
		for(i=0; i<framelen; ++i) {
			pixels[3*i] *= noise[i];
			pixels[3*i+1] *= noise[i];
			pixels[3*i+2] *= noise[i];
		}
    PyMem_Free(noise);
    PyMem_Free(scaledX);
    PyMem_Free(scaledY);
    PyMem_Free(scaledZ);
	Py_RETURN_NONE;

dealloc_scaledZ:
    PyMem_Free(scaledZ);
dealloc_scaledY:
    PyMem_Free(scaledY);
dealloc_scaledX:
    PyMem_Free(scaledX);
	return PyErr_NoMemory();
}

static PyMethodDef methods[] = {
   { "render", (PyCFunction)py_render, METH_VARARGS,
    },
    {NULL}  /* Sentinel */
};


PyMODINIT_FUNC initcplasma(void)
{
    Py_InitModule3("cplasma", methods,
                   "Quicker plasma color effect done in C.");
	assert(m != NULL);
	import_array();
	return;
}


// Copied from source of python noise module
#define lerp(t, a, b) ((a) + (t) * ((b) - (a)))

float inline
grad3(const int hash, const float x, const float y, const float z)
{
	const int h = hash & 15;
	return x * GRAD3[h][0] + y * GRAD3[h][1] + z * GRAD3[h][2];
}

float
noise3(float x, float y, float z, const int repeatx, const int repeaty, const int repeatz,
	const int base)
{
	float fx, fy, fz;
	int A, AA, AB, B, BA, BB;
	int i = (int)floorf(fmodf(x, repeatx));
	int j = (int)floorf(fmodf(y, repeaty));
	int k = (int)floorf(fmodf(z, repeatz));
	int ii = (int)fmodf(i + 1,  repeatx);
	int jj = (int)fmodf(j + 1, repeaty);
	int kk = (int)fmodf(k + 1, repeatz);
	i = (i & 255) + base;
	j = (j & 255) + base;
	k = (k & 255) + base;
	ii = (ii & 255) + base;
	jj = (jj & 255) + base;
	kk = (kk & 255) + base;

	x -= floorf(x); y -= floorf(y); z -= floorf(z);
	fx = x*x*x * (x * (x * 6 - 15) + 10);
	fy = y*y*y * (y * (y * 6 - 15) + 10);
	fz = z*z*z * (z * (z * 6 - 15) + 10);

	A = PERM[i];
	AA = PERM[A + j];
	AB = PERM[A + jj];
	B = PERM[ii];
	BA = PERM[B + j];
	BB = PERM[B + jj];

	return lerp(fz, lerp(fy, lerp(fx, grad3(PERM[AA + k], x, y, z),
									  grad3(PERM[BA + k], x - 1, y, z)),
							 lerp(fx, grad3(PERM[AB + k], x, y - 1, z),
									  grad3(PERM[BB + k], x - 1, y - 1, z))),
					lerp(fy, lerp(fx, grad3(PERM[AA + kk], x, y, z - 1),
									  grad3(PERM[BA + kk], x - 1, y, z - 1)),
							 lerp(fx, grad3(PERM[AB + kk], x, y - 1, z - 1),
									  grad3(PERM[BB + kk], x - 1, y - 1, z - 1))));
}

