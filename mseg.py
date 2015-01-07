#!/usr/bin/env python3

""" Import and process microsegment data and export to JSON """

# Import needed packages


def grouper(prev_line, curr_line, consume, eqstock):
    """ Combine data or create new data vectors where appropriate """

    # Fragile to changes in the column definition in the input file
    if curr_line[0:5] == prev_line[0:5]:
        eqstock.append(curr_line[6])
        consume.append(curr_line[-1])
    return (consume, eqstock)


if __name__ == '__main__':
    main()
