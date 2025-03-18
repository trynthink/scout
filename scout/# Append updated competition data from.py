            # Append updated competition data from measure to
            # list of competition data across all measures
            meas_prepped_compete.append(comp_data_dict)
            # Append fuel switching split information, if applicable
            meas_eff_fs_splt.append(fs_splits_dict)
            # Append sector shape information, if applicable
            meas_prepped_shapes.append(shapes_dict)
            # Delete 'handyvars' measure attribute (not relevant to
            # analysis engine)
            del m.handyvars
            # Delete 'tsv_features' measure attributes
            # (not relevant) for individual measures
            if not isinstance(m, MeasurePackage):
                del m.tsv_features
                # Delete individual measure attributes used to link heating/
                # cooling microsegment turnover and switching rates
                del m.linked_htcl_tover
                del m.linked_htcl_tover_anchor_eu
                del m.linked_htcl_tover_anchor_tech
                # If backup fuel fraction data exist (will be dataframe), convert to simple flag for
                # JSON write-out and subsequent use in run
                if m.backup_fuel_fraction is not None:
                    m.backup_fuel_fraction = True
                del m.ref_analogue
                del m.add_elec_infr_cost
            # For measure packages, replace 'contributing_ECMs'
            # objects list with a list of these measures' names and remove
            # unnecessary heating/cooling equip/env overlap data
            if isinstance(m, MeasurePackage):
                m.contributing_ECMs = [
                    x.name for x in m.contributing_ECMs]
                del m.htcl_overlaps
                del m.contributing_ECMs_eqp
                del m.contributing_ECMs_env
            # Append updated measure __dict__ attribute to list of
            # summary data across all measures
            meas_prepped_summary.append(m.__dict__)

        return meas_prepped_compete, meas_prepped_summary, meas_prepped_shapes, \
            meas_eff_fs_splt