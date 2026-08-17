from .cli import main

# the guard matters: multiprocessing spawn workers (postprod --jobs)
# re-import __main__ as __mp_main__ and must not re-run the CLI
if __name__ == '__main__':
	main()
