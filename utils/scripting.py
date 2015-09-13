import sys


def require_db_write_acknowledgement():
    """Warn the command line user that proceeding modifies the database,
    requiring acknowledgement.
    """
    proceed = False

    while not proceed:
        sys.stdout.write('This script may modify the database. '
                         'Proceed? (yes/no): ')
        response = raw_input()
        if response == 'no':
            sys.stdout.write('Okay. Goodbye!\n')
            sys.exit(0)
        elif response != 'yes':
            sys.stdout.write('Please try again, '
                             'responding "yes" or "no"\n')
            continue
        else:
            proceed = True

    return